class XcomError(Exception):
    def __init__(self, message = '', thrower = None):
        super().__init__(message)
        self.thrower = thrower

class ParseError(XcomError):
    pass

class ResponseError(XcomError):
    pass

class StatusError(XcomError):
    pass

class ClientTimeoutError(XcomError):
    pass

class CommunicationError(XcomError):
    pass