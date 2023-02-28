from connections import UnclosableConnection
from jackhammer import HttpJackHammer, ResultHandler
from threads import ClientTaskControl

def task(conn: UnclosableConnection, handler: ResultHandler) -> None:
    """
    Intended to do minimal result processing.
    Basically only check if the response has the correct status or certain
    headers set and send a message with all the data you need to either the
    result or error queue for processing.
    
    Intended pattern:

    conn.request('GET', /somepath)
    with conn.getresponse() as res:
        code = res.status
        ...
    if code == 200:
        handler.put_succes(...)
    else:
        handler.put_error(...)

    The connection is returned to the pool as soon as you exit the with block.
    So the less time you spend within the with context, the faster the connection can
    be used again!
    """


def on_error(event: object, task_control: ClientTaskControl) -> None:
    """
    Is triggered whenever an event is consumed from the error queue.
    Events are put on the error queue by calling handler.put_error(...) in the above task function.
    the ClientTaskControl object allows you to programatically stop execution if you wish.
    """

def on_success(event: object, task_control: ClientTaskControl) -> None:
    """
    Is triggered whenever an event is consumed from the success queue.
    Events are put on the success queue by calling handler.put_success(...) in the above task function.
    the ClientTaskControl object allows you to programatically stop execution if you wish.
    """

if __name__ == "__main__":
    http_hammer = HttpJackHammer(task, on_error, on_success)
    print('Running (press Ctrl + C to abort) ...')
    thread = http_hammer.start("$TARGET_HOST", "$NUM_CONNECTIONS")
    thread.join()