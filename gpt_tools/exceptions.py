
class BrowserError(Exception):
    """An arbitrary error occurred in the browser - see error message for details"""
    pass

class ServerError(Exception):
    """An arbitrary error occurred in the server - see error message for details"""
    pass

class PageNotFound(Exception):
    """ The 404 - page not found error"""
    pass