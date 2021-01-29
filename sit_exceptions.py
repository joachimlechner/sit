# Description: SIT - Svn with gIT extensions, sit exceptions
# Author:      Joachim Lechner
# Licence:     GNU GENERAL PUBLIC LICENSE, Version 2, June 1991
# Source:      https://github.com/joachimlechner/sit

class SitException(Exception):
    name = "SitException"
    message = ""

    def __init__(self, message):
        self.message = message

    def __str__(self):
        if self.message:
            return self.name + ': ' + self.message
        else:
            return self.name + ' has been raised'

class SitExceptionParseError(SitException):
    name = "SitExceptionParseError"

class SitExceptionInternalFatalError(SitException):
    name = "SitExceptionInternalFatalError"

class SitExceptionDecode(SitException):
    name = "SitExceptionDecode"

class SitExceptionAbort(SitException):
    name = "SitExceptionAbort"

class SitExceptionSelect(SitException):
    name = "SitExceptionSelect"

class SitExceptionExecute(SitException):
    name = "SitExceptionExecute"

