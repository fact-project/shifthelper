from __future__ import absolute_import
import pkg_resources

from .communication import TwilioInterface, TelegramInterface, NoCaller
from .checks import Alert
from .checks.qla import FlareAlert
from .checks.webdim import RelativeCameraTemperatureCheck
from .checks.webdim import CurrentCheck
from .checks.webdim import MainJsStatusCheck
from .checks.webdim import WeatherCheck

__version__ = pkg_resources.require('shifthelper')[0].version
