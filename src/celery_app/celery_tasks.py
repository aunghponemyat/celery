from celery_app import app
import time
import random

@app.task(time_limit=60, soft_time_limit=50)
def start_task(name: str):
    new_value = 3 + 3
    print(f"Hi I'm new again in {name}")
    time.sleep(13)
    get_called()
    return new_value

def get_called():
    print("Hello! This is a function being called")
    time.sleep(13)
    value = random.randint(1, 100)
    process(value)

def process(value: int):
    if value % 2 == 0:
        print("Ah.. Value is right")
    else:
        print("Oops. Not expected")
