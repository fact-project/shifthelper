'''
create custom exceptions to better handle
the different problems that can occure
'''


class FACTException(ValueError):
    pass


class SecurityException(FACTException):
    pass


class QLAException(FACTException):
    pass


class DataTakingException(FACTException):
    pass
