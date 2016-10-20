import logging
import sys
import os
import time

from pythonjsonlogger.jsonlogger import JsonFormatter


def config_logging(to_console=False):
    dot_shifthelper_dir = os.path.join(os.environ['HOME'], '.shifthelper')
    os.makedirs(dot_shifthelper_dir, exist_ok=True)

    logfile_handler = logging.handlers.TimedRotatingFileHandler(
        filename=os.path.join(dot_shifthelper_dir, 'shifthelper.log'), 
        when='D', interval=1,  # roll over every day.
        backupCount=300,       # keep 300 days back log
        utc=True,
    )
    logfile_handler.setLevel(logging.DEBUG)
    formatter = JsonFormatter()
    formatter.converter = time.gmtime  # use utc in log
    logfile_handler.setFormatter(formatter)

    log = logging.getLogger("custos")
    log.setLevel(logging.DEBUG)
    log.addHandler(logfile_handler)

    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    log.addHandler(logfile_handler)

    if to_console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logging.getLogger().addHandler(ch)