import http.client as htc
import queue
import sys
import threading
from typing import Callable

class ManagedResponseCtx(object):
    def __init__(self, response: htc.HTTPResponse):
        self.response = response

    def __enter__(self) -> htc.HTTPResponse:
        return self.response

    def __exit__(self, exc_type, exc_value, exc_tb):
        if not self.response.isclosed():
            self.response.read()
            self.response.close()

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

class ConnectionPoolQueue(object):
    def __init__(self, size):
        self.__internal_q = queue.Queue(size)
    
    def get(self) -> Connection:
        return self.__internal_q.get()

    def put(self, connection: Connection) -> None:
        self.__internal_q.put(connection)
    
    def size(self) -> int:
        return self.__internal_q.qsize()

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

class ResultHandler(object):
    def __init__(self, success_q, error_q):
        self.__success_q = success_q
        self.__error_q = error_q

    def put_error(self, msg):
        self.__error_q.put(msg)

    def put_success(self, msg):
        self.__success_q.put(msg)

class TaskControl(object):

    def __init__(self):
        self.__thread_control_q = queue.Queue(1)
    
    def running(self) -> bool:
        return self.__thread_control_q.qsize() == 1

    def start(self) -> None:
        self.__thread_control_q.put('RUNNING')
    
    def stop(self) -> None:
        self.__thread_control_q.get()

class ClientTaskControl(object):

    def __init__(self, controller: TaskControl) -> None:
        self.__internal_controller = controller

    def stop(self) -> None:
        self.__internal_controller.stop()


class HttpTaskManager(object):

    def __init__(self, task: Callable[[UnclosableConnection, ResultHandler], None], on_error: Callable[[object, ClientTaskControl], None], on_success: Callable[[object, ClientTaskControl], None]) -> None:
        self.__task = task
        self.__on_error = on_error
        self.__on_success = on_success
        self.__task_control = TaskControl()
        self.__client_task_control = ClientTaskControl(self.__task_control)
        self.__success_q = queue.Queue()
        self.__error_q = queue.Queue()
        self.__task_result_handler = ResultHandler(self.__success_q, self.__error_q)

    def start(self, host: str, num_connections: int) -> threading.Thread:
        self.__connection_pool = ConnectionPool(num_connections)
        self.__connection_pool.connect(host)
        thread = threading.Thread(target=self.__launch_threads())
        thread.start()
        return thread

    def __launch_threads(self) -> None:
        try:
            threads = []
            for i in range(self.__connection_pool.capacity()):
                threads.append(threading.Thread(target=self.__task_loop))
            threads.append(threading.Thread(target=self.__success_watcher_loop))
            threads.append(threading.Thread(target=self.__error_watcher_loop))

            self.__task_control.start()
            for t in threads:
                t.start()
            
            # block execution till interupt or natural end
            while self.__task_control.running():
                pass
        except KeyboardInterrupt:
            self.__task_control.stop()
        finally:
            for t in threads:
                t.join()
            self.__connection_pool.close_connections()

    def __success_watcher_loop(self):
        while self.__task_control.running():
            if self.__success_q.qsize() > 0:
                self.__on_success(self.__success_q.get(), self.__client_task_control)

    def __error_watcher_loop(self):
        while self.__task_control.running():
            if self.__error_q.qsize() > 0:
                self.__on_error(self.__error_q.get(), self.__client_task_control)

    def __task_loop(self):
        while self.__task_control.running():
            with self.__connection_pool.get_connection() as conn:
                self.__task(conn, self.__task_result_handler)
        