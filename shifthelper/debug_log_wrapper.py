from inspect import getmodule
from wrapt import decorator
import logging


@decorator
def log_call_and_result(wrapped, instance, args, kwargs):
    log = logging.getLogger(getmodule(wrapped).__name__)
    result = wrapped(*args, **kwargs)
    log.debug('%s -> %s', wrapped.__name__, result)
    return result
