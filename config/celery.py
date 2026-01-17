"""
Celery configuration for async tasks.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('networth')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'update-exchange-rates-daily': {
        'task': 'currencies.tasks.update_exchange_rates',
        'schedule': crontab(hour=9, minute=0),  # Run daily at 9:00 AM UTC
    },
    # TODO: Create networth.tasks.create_daily_snapshots task
    # 'create-daily-networth-snapshots': {
    #     'task': 'networth.tasks.create_daily_snapshots',
    #     'schedule': crontab(hour=0, minute=0),  # Run daily at midnight UTC
    # },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f'Request: {self.request!r}')
