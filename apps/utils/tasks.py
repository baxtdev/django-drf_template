from celery import shared_task
from django.db.transaction import atomic

from .utils import send_code

@shared_task
def send_code_background(id,code,phone):
    result = send_code(
        id,
        code,
        phone
    )

    return result

@shared_task
def send_notification_background(phone):
    pass





