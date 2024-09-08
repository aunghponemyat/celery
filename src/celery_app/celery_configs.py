from celery_app.configs import Settings, get_settings

settings: Settings = get_settings()

broker_url = settings.broker
imports = f"{settings.app}.celery_tasks"


result_backend = f"db+{settings.tidb_dsn}"
database_table_names = {
    'task': settings.task_table,
    'group': settings.task_table,
}

task_time_limit = 30
task_track_started = True