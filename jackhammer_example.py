import jackhammer
import sys

def task(conn, handler):
    conn.request('GET', '/')
    with conn.getresponse() as res:
        status = res.status
    if status == 200:
        handler.put_success("Server responded with 200 OK")
    else:
        handler.put_error({'status': status, 'msg': 'Got unexpected response'})

def on_error(event, task_control):
    if event['status'] == 301 or event['status'] == 302:
        print('Got redirect.')
    else:
        print(f"{event['msg']} {event['status']}. Aborting...")
        task_control.stop()

def on_success(msg, task_control):
    print(f"{msg}. My first correct request, yay! :)")
    task_control.stop()

if __name__ == "__main__":
    if len(sys.argv) != 3 or not sys.argv[2].isdigit():
        print(f"\nUsage: python3 jackhammer_example.py HOST NUM_CONNECTIONS")
        sys.exit(0)
    http_hammer = jackhammer.HttpJackHammer(task, on_error, on_success)
    print('Running (press Ctrl + C to abort) ...')
    thread = http_hammer.start(sys.argv[1], int(sys.argv[2]))
    thread.join()