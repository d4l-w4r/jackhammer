import queue

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