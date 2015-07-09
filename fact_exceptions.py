'''
create custom exceptions to better handle
the different problems that can occure
'''


class FACTException(ValueError):
    __name__ = 'FACTException'


class SecurityException(FACTException):
    __name__ = 'SecurityException'


class QLAException(FACTException):
    __name__ = 'QLAException'


class DataTakingException(FACTException):
    __name__ = 'DataTakingException'
