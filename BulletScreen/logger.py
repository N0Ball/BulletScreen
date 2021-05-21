import logging
import colorlog

def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    format      = '%(asctime)s - %(log_color)s%(levelname)-8s%(reset)s%(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    cformat = format
    f = colorlog.ColoredFormatter(cformat, date_format,
            log_colors = { 
                'DEBUG'   : 'reset',
                'INFO' : 'cyan',
                'WARNING' : 'bold_yellow',
                'ERROR': 'bold_red',
                'CRITICAL': 'bold_red' 
            })
    ch = logging.StreamHandler()
    ch.setFormatter(f)
    root.addHandler(ch)

setup_logging()
log = logging.getLogger(__name__)