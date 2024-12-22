from django.db.models.signals import post_save,pre_save,post_migrate
from django.dispatch import receiver
from django.db.transaction import atomic
from .models import PhoneNumberChange,ResetPasword
from apps.utils.utils import send_code,generate_code,generate_sms_id
from apps.utils.tasks import send_code_background




@receiver(post_save, sender=PhoneNumberChange)
@atomic
def send_sms_on_phone_change(sender, instance:PhoneNumberChange, created, **kwargs):
    if created and not instance.is_test:
        return
        phone_number = str(instance.new_phone_number)
        id = generate_sms_id()
        send_code_background.apply_async(args=[id,instance.code,phone_number], countdown=10)


@receiver(post_save, sender=ResetPasword)
@atomic
def send_sms_on_reset_password(sender, instance: ResetPasword, created, **kwargs):
    if created and not instance.is_test:
        return
        phone_number = str(instance.user.phone)
        id = generate_sms_id()
        reult = send_code_background.apply_async(args=[id, instance.code,phone_number],countdown=10)