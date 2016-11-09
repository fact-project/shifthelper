import logging
import logging.handlers
import sys
import os
import time

from pythonjsonlogger.jsonlogger import JsonFormatter


def config_logging(to_console=False, level=logging.DEBUG):
    dot_shifthelper_dir = os.path.join(os.environ['HOME'], '.shifthelper')
    os.makedirs(dot_shifthelper_dir, exist_ok=True)

    logdir = os.environ.get('SHIFTHELPER_LOGDIR', dot_shifthelper_dir)

    text_logfile_handler = logging.handlers.TimedRotatingFileHandler(
        filename=os.path.join(logdir, 'shifthelper.log'),
        when='D',
        interval=1,
        backupCount=300,
        utc=True,
    )
    text_logfile_handler.setLevel(level)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter.converter = time.gmtime  # use utc in log
    text_logfile_handler.setFormatter(formatter)

    logfile_handler = logging.handlers.TimedRotatingFileHandler(
        filename=os.path.join(logdir, 'shifthelper_log.jsonl'),
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
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s'
    )
    formatter.converter = time.gmtime  # use utc in log
    stream_handler.setFormatter(formatter)

    for logger_name in ('shifthelper', 'custos'):
        log = logging.getLogger(logger_name)
        log.setLevel(level)
        log.addHandler(logfile_handler)
        log.addHandler(text_logfile_handler)

        if to_console:
            log.addHandler(stream_handler)

    log = logging.getLogger('root')
    log.setLevel(logging.INFO)
    log.addHandler(logfile_handler)
    log.addHandler(text_logfile_handler)
    if to_console:
        log.addHandler(stream_handler)
