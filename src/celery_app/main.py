import redis
import os
import signal
import time
import subprocess
import threading
from celery_app.celery_tasks import start_task
from celery.result import AsyncResult
from celery_app import app

r = redis.Redis()

def start_worker(queue_name):
    process = subprocess.Popen([
        'celery', '-A', 'celery_app', 'worker', 
        '-Q', queue_name, 
        '--concurrency=1',
        '--loglevel=warning',
        f'--hostname={queue_name}@%h',
    ])
    print(f"Started worker with PID {process.pid}")
    return process.pid

def task_heartbeat(queue_name):
    r.set(f'worker:{queue_name}:last_heartbeat', time.time())

def check_worker_idle(queue_name, pid, task_id, timeout=10, grace_period=10):
    # Wait for the grace period before starting idle checks
    time.sleep(grace_period)
    task_completed = False
    last_heartbeat = time.time()
    # idle_time = 0

    while True:
        if r.get(f'worker:{queue_name}:task_id'):
            task_id = r.get(f'worker:{queue_name}:task_id').decode('utf-8')
        
        result = AsyncResult(task_id, app=app)
        
        # Check if task has completed
        if not task_completed:
            if result.ready():
                if result.successful() or result.failed():
                    task_completed = True
                    r.delete(f'worker:{queue_name}:task_id')
                    print(f"Task {task_id} has completed")
                    last_heartbeat = time.time()
            else:
                task_heartbeat(queue_name)
                last_heartbeat = float(r.get(f'worker:{queue_name}:last_heartbeat') or 0)

        # Check if a new task has entered the queue
        task_status = r.get(f'worker:{queue_name}:new_task')
        if task_status:
            task_heartbeat(queue_name)
            task_completed = False
            r.delete(f'worker:{queue_name}:new_task')

        # If task is completed and the worker has been idle, shut down the worker
        if task_completed and (time.time() - last_heartbeat > timeout):
            idle_time = timeout
            while idle_time > 0:
                task_status = r.get(f'worker:{queue_name}:new_task')
                
                if task_status:
                    # Reset the countdown if a new task arrives
                    print("New task detected. Resetting shutdown countdown.")
                    task_completed = False
                    r.delete(f'worker:{queue_name}:new_task')
                    break  # Exit the countdown loop

                # Print the countdown in regular intervals
                # print(f"Worker shutdown in: {idle_time} seconds")
                time.sleep(1)  # Sleep for 1 second between countdown updates
                idle_time -= 1

            # If the countdown reaches 0 without a new task, shut down the worker
            if idle_time == 0:
                print(f"Worker {queue_name} has been idle for {timeout} seconds. Shutting down...")
                os.kill(pid, signal.SIGTERM)
                break  # Exit the main loop once the worker is shut down

        time.sleep(1)  # Sleep for a bit before checking again

def task_wrapper(name):
    task = start_task.apply_async(args=(name,), queue=name)
    print(task.id, "submitted")
    if r.get(f'worker:{name}:new_task') is None:
        r.set(f'worker:{name}:new_task', 1)
    return task.id

def begin(name):
    # Check if the worker process is already running
    result = subprocess.run(
        f"ps aux | grep 'celery -A celery_app worker -Q {name} --concurrency=1 --loglevel=warning --hostname={name}@%h' | grep -v grep",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    print(result.stdout, result.returncode)
    if result.returncode == 0:
        print("Worker process is already running")
        task_id = task_wrapper(name)
    else:
        # Start a new worker and monitor it
        pid = start_worker(name)
        task_id = task_wrapper(name)
        threading.Thread(target=check_worker_idle, args=(name, pid, task_id)).start()
    old_task_key = f'worker:{name}:task_id'
    if r.exists(old_task_key):
        r.delete(old_task_key)
    r.set(f'worker:{name}:task_id', task_id)

if __name__ == "__main__":
    name = input("Enter name: ")
    begin(name)
