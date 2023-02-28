import http.client as htc
from response import ManagedResponseCtx
from pooling import ConnectionPoolQueue

class Connection(object):
    def __init__(self, cid: str, http_con: htc.HTTPConnection):
        self.cid = cid
        self.http_con = http_con

class UnclosableConnection(object):
    def __init__(self, httpConnection: Connection):
        self.__conn = httpConnection
    
    def request(self, method, url, body=None, headers={}, encode_chunked=False) -> None:
        self.__conn.http_con.request(method, url, body=body, headers=headers, encode_chunked=encode_chunked)

    def getresponse(self) -> ManagedResponseCtx:
        response = self.__conn.http_con.getresponse()
        return ManagedResponseCtx(response)



class ManagedConnectionCtx(object):
    def __init__(self, connection_pool: ConnectionPoolQueue):
        self.__conn_q = connection_pool

    def __enter__(self) -> UnclosableConnection:
        self.__active_con = self.__conn_q.get()
        return UnclosableConnection(self.__active_con)

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.__conn_q.put(self.__active_con)