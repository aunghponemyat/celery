from importlib.metadata import PackageNotFoundError, version
from celery import Celery

__package__ = "celery_app"
__name__ = "celery_app"
try:
    __version__ = version(__package__)
except PackageNotFoundError:
    __version__ = "unknown"
    
app = Celery("celery_app")
app.config_from_object("celery_app.celery_configs")
app.conf.task_default_queue = 'my-queue'

