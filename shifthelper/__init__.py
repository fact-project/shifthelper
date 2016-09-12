import pkg_resources
__version__ = pkg_resources.require('shifthelper')[0].version

import logging
import logging.handlers
import time
import os
from . import tools