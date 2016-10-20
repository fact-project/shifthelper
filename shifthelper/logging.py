import logging
import logging.handlers
import sys
import os
import time

from pythonjsonlogger.jsonlogger import JsonFormatter


def config_logging(to_console=False, level=logging.DEBUG):
    dot_shifthelper_dir = os.path.join(os.environ['HOME'], '.shifthelper')
    os.makedirs(dot_shifthelper_dir, exist_ok=True)

    logfile_handler = logging.handlers.TimedRotatingFileHandler(
        filename=os.path.join(dot_shifthelper_dir, 'shifthelper_log.jsonl'),
        when='D', interval=1,  # roll over every day.
        backupCount=300,       # keep 300 days back log
        utc=True,
    )
    logfile_handler.setLevel(level)
    formatter = JsonFormatter(fmt=(
         '%(asctime)s,%(levelno)s,%(name)s,%(module)s'
         ',%(funcName)s,%(message)s,%(filename)s,%(lineno)s'
    ))
    formatter.converter = time.gmtime  # use utc in log
    logfile_handler.setFormatter(formatter)

    log = logging.getLogger("custos")
    log.setLevel(level)
    log.addHandler(logfile_handler)

    log = logging.getLogger(__name__)
    log.setLevel(level)
    log.addHandler(logfile_handler)

    if to_console:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s'
        )
        stream_handler.setFormatter(formatter)
        logging.getLogger().addHandler(stream_handler)
