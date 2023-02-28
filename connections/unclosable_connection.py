from .connection import Connection
from .response import ManagedResponseCtx

class UnclosableConnection(object):
    def __init__(self, httpConnection: Connection):
        self.__conn = httpConnection
    
    def request(self, method, url, body=None, headers={}, encode_chunked=False) -> None:
        self.__conn.http_con.request(method, url, body=body, headers=headers, encode_chunked=encode_chunked)

    def getresponse(self) -> ManagedResponseCtx:
        response = self.__conn.http_con.getresponse()
        return ManagedResponseCtx(response)