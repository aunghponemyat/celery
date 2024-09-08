## Python Celery Task Tracker

- Intended for background processing of python I/O bound tasks inside Celery using threads for monitoring and redis for task queue handler.

- Task IDs and their life cycle will also be managed by a logic that is implemeted upon the mechanism supported by redis keys.

### App Usage

```
user$ poetry shell
```
```
user$ python src/celery_app/main.py
```

This command triggers celery to use the
dedicated queue and worker name defined by the
custom user input.
```
user$ Enter name: <your-desired-name>
```
