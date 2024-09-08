import redis
import os
import signal
import time
import subprocess
import threading
from celery_app.celery_tasks import start_task
from celery.result import AsyncResult
r = redis.Redis()

def start_worker(queue_name):
    process = subprocess.Popen([
        'celery', '-A', 'celery_app', 'worker', 
        '-Q', queue_name, 
        '--concurrency=1',
        '--loglevel=warning',
        f'--hostname={queue_name}@%h',
    ])
    print(process.pid)
    return process.pid

def task_heartbeat(queue_name):
    r.set(f'worker:{queue_name}:last_heartbeat', time.time())

def check_worker_idle(queue_name, pid, timeout=10, grace_period=10):
    # Wait for the grace period before starting idle checks
    time.sleep(grace_period)
    while True:
        last_heartbeat = float(r.get(f'worker:{queue_name}:last_heartbeat') or 0)
        if time.time() - last_heartbeat > timeout:
            print(f"Worker {queue_name} has been idle for more than {timeout} seconds. Shutting down...")
            os.kill(pid, signal.SIGTERM)
            break
        time.sleep(1)

def task_wrapper(name):
    task = start_task.apply_async(args=(name,), queue=name)
    print(task.id, "submitted")
    task_heartbeat(name)  # Update heartbeat after task is queued
    # task.get()
    return task.id

def begin(name):
    result = subprocess.run(
        f"ps aux | grep 'celery -A celery_app worker -Q {name} --concurrency=1 --loglevel=warning --hostname={name}@%h' | grep -v grep",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    print(result.stdout, result.returncode)
    if result.returncode == 0:
        print("Worker process is already running")
        task_wrapper(name)
    else:
        pid = start_worker(name)
        threading.Thread(target=check_worker_idle, args=(name, pid)).start()
        task_id = task_wrapper(name)
        print(task_id)

if __name__ == "__main__":
    name = input("Enter name: ")
    begin(name)
