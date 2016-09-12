import pkg_resources
__version__ = pkg_resources.require('shifthelper')[0].version

import logging
import logging.handlers
import time
import os
from . import tools

logdir = os.path.join(os.environ['HOME'], '.shifthelper')
os.makedirs(logdir, exist_ok=True)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
logfile_path = os.path.join(logdir, 'shifthelper.log')
logfile_handler = logging.handlers.TimedRotatingFileHandler(
    filename=logfile_path, 
    when='D', interval=1,  # roll over every day.
    backupCount=300,       # keep 300 days back log
    utc=True
)
logfile_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    fmt='%(asctime)s - %(levelname)s - %(name)s | %(message)s',
    #datefmt='%Y-%m-%dT%H:%M:%S',
)
formatter.converter = time.gmtime  # use utc in log
logfile_handler.setFormatter(formatter)
log.addHandler(logfile_handler)
logging.getLogger('py.warnings').addHandler(logfile_handler)
logging.captureWarnings(True)