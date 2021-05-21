import asyncio
import websockets
import json
import os

from . import HOST, PORT, PASS
from .logger import log

class BulletScreen:

    users = {}
    targetsocket = None
    COLORS = ["blue", "puple", "pink", "cyan", "white", "orange", "gold", "greenyellow", "deepskyblue"]

    def __init__(self):

        self.server = websockets.serve(self.server, HOST, PORT)
        log.info(f"Listening on {HOST}: {PORT}")

    def run(self):

        asyncio.get_event_loop().run_until_complete(self.server)
        asyncio.get_event_loop().run_forever()

    # def state_event(self):
    #     return json.dumps({"type": "state", **self.STATE})

    # def users_event(self):
    #     return json.dumps({"type": "users", "count": len(self.users)})

    # async def notify_state(self):
    #     if self.users: 
    #         message = self.state_event()
    #         await asyncio.wait([user["socket"].send(message) for user in self.users])

    # async def notify_users(self):
    #     if self.users:
    #         message = self.users_event()
    #         await asyncio.wait([user["socket"].send(message) for user in self.users])

    def generate_id(self):

        while True:

            id = os.urandom(32)

            if id in self.users:
                continue

            return id

    async def broadcast (self, send_user, msg):
        log.info(f"Broadcasted {msg}")
        if self.users:
            await asyncio.wait([self.users[user]["socket"].send(
                json.dumps({
                "header": "GET MSG",
                "data": {
                    "msg": msg,
                    "name": send_user["name"],
                    "color": send_user["color"]
                }
            })) for user in self.users])

    async def register(self, websocket):
        log.info(f'Get registered at {websocket.remote_address[0]}:{websocket.remote_address[1]}')
        
        id = repr(self.generate_id())

        self.users.update(
            {
                id: {
                    "name": None,
                    "id": id,
                    "socket": websocket,
                    "color": self.COLORS[(os.urandom(1)[0] % len(self.COLORS))]
                }
            })

        await websocket.send(json.dumps({
            "header": "Reg Response",
            "data": id
        }))
    
    async def unregister(self, websocket):

        log.info(f'Get Unregistered at {websocket.remote_address[0]}: {websocket.remote_address[1]}')

        for user in self.users:

            if self.users[user]["socket"] == websocket:
                del self.users[user]
                break

    async def set_name(self, user, name):

        if name == '' :
            log.warn(f'{user["id"]} trying to set empty name')
            await user["socket"].send(json.dumps({
                "header": "ERROR",
                "data": "Empty Name"
            }))
            return 
        
        log.info(f'{user["id"]} trying to set name to {name}')

        user["name"] = name

    async def send_msg(self, user, msg):

        try:

            if user["name"] != None:

                log.info(f'<{user["name"]}> sent <{msg}>')

                await self.targetsocket.send(json.dumps({
                    "header": "GET MSG",
                    "data": {
                        "msg": msg,
                        "color": user["color"]
                    }
                }))

            else:

                log.warn(f'id: {user["id"]} send with no name!')

                await user["socket"].send(json.dumps({
                    "header": "ERROR",
                    "data": "No name is set"
                }))

        except Exception as e:

            log.error(e)

            await user["socket"].send(json.dumps({
                "header": "ERROR",
                "data": e
            }))

    async def set_target(self, user, pas):

        socket = user["socket"]

        if pas == PASS:

            log.info(f"Target logged in at {socket.remote_address[0]}: {socket.remote_address[1]}")
            self.targetsocket = user["socket"]

        else:
            log.warn(f"Someone trying to log to target by wrong password at {socket.remote_address[0]}: {socket.remote_address[1]}")

        del self.users[user["id"]]

    async def handle(self, msg):

        try:

            user = self.users[msg["id"]]

        except Exception as e:

            log.warn(f'Unauthorized msg detected! with invalid id: {e}')

        try:
            operation = msg["header"]
            data = msg["data"]
            
            if operation == "SET TARGET":
                await self.set_target(user, data)
                return
            
            if operation == "SET NAME":

                await self.set_name(user, data)
                return

            if operation == "SEND MSG":

                if self.targetsocket is None:
                    log.error(f"msg recieved without target logged")
                    return

                await self.send_msg(user, data)
                await self.broadcast(user, msg)
                return
            
        except Exception as e:
            log.error(f"Problem meet!{e}")
            return

    async def server(self, websocket, path):
        await self.register(websocket)
        try:
            async for message in websocket:
                await self.handle(json.loads(message))
        finally:
            await self.unregister(websocket)