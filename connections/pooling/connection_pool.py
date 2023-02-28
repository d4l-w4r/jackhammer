from ..connection import Connection
from ..unclosable_connection import UnclosableConnection
from .connection_pool_queue import ConnectionPoolQueue
import http.client as htc

class ManagedConnectionCtx(object):
    def __init__(self, connection_pool: ConnectionPoolQueue):
        self.__conn_q = connection_pool

    def __enter__(self) -> UnclosableConnection:
        self.__active_con = self.__conn_q.get()
        return UnclosableConnection(self.__active_con)

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.__conn_q.put(self.__active_con)

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