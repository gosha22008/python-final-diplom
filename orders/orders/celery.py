import os
from django.conf import settings
from celery import Celery
# from __future__ import absolute_import


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orders.settings')
celery_app = Celery('orders')
celery_app.config_from_object('django.conf:settings', namespace="CELERY")
celery_app.autodiscover_tasks()
