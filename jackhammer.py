from connections import ConnectionPool
from connections import UnclosableConnection
import queue
import threading
from threads import ClientTaskControl, TaskControl
from typing import Callable

class ResultHandler(object):
    def __init__(self, success_q, error_q):
        self.__success_q = success_q
        self.__error_q = error_q

    def put_error(self, msg):
        self.__error_q.put(msg)

    def put_success(self, msg):
        self.__success_q.put(msg)

class HttpJackHammer(object):

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