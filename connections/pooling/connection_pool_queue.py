from ..connection import Connection
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