from connection import Connection, ManagedConnectionCtx
import http.client as htc
import queue


class ConnectionPoolQueue(object):
    def __init__(self, size):
        self.__internal_q = queue.Queue(size)
    
    def get(self) -> Connection:
        return self.__internal_q.get()

    def put(self, connection: Connection) -> None:
        self.__internal_q.put(connection)
    
    def size(self) -> int:
        return self.__internal_q.qsize()

class ConnectionPool(object):
    def __init__(self, size) -> None:
        self.__max_q_size = size
        self.__pool_q = ConnectionPoolQueue(size)

    def capacity(self) -> int:
        return self.__max_q_size

    def connect(self, host: str) -> None:
        for i in range(self.__max_q_size):
            self.__pool_q.put(Connection(f"{i}-{host}-con", htc.HTTPSConnection(host)))

    def close_connections(self) -> None:
        while self.__pool_q.size() > 0:
            self.__pool_q.get().http_con.close()

    def get_connection(self) -> ManagedConnectionCtx:
        return ManagedConnectionCtx(self.__pool_q)