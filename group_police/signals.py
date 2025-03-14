from django.db.models.signals import post_save, pre_delete, m2m_changed
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import IoTUser, UserLog, IoTDevice, IoTDeviceLog


@receiver(post_save, sender=IoTUser)
def log_create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserLog.objects.create(
            status='created',
            user=instance,
            description=f'Пользователь с именем [{instance.username}] был успешно создан'
        )


@receiver(post_save, sender=IoTDevice)
def log_create_device(sender, instance, created, **kwargs):
    if created:
        IoTDeviceLog.objects.create(
            status='created',
            device=instance,
            description=f'Устройство с идентификатором [{instance.device_name}] было добавлено в систему'
        )


@receiver(pre_delete, sender=IoTUser)
def log_user_deletion(sender, instance, **kwargs):
    UserLog.objects.create(
        status='deleted',
        user=instance,
        description=f'Пользователь с именем [{instance.username}] был удален'
    )


@receiver(m2m_changed, sender=IoTUser)
def log_user_group_changed(sender, instance, **kwargs):
    UserLog.objects.create(
        status='changed',
        user=instance,
        description=f'Пользователь с именем [{instance.username}] был удален'
    )
