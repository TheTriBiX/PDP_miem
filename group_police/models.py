import datetime
from email.policy import default

from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models


def log_user_to_device(device, user, status, description):
    UserToDeviceLog.objects.create(
        status=status,
        device=device,
        user=user,
        description=description,
    )


class IoTUser(AbstractUser):
    roles = models.ManyToManyField(Group, related_name="iot_users")  # RBAC: Роли пользователей
    attributes = models.JSONField(default=dict, blank=True)  # ABAC: Дополнительные атрибуты
    allowed_iot_groups = models.ManyToManyField('IoTGroup')


class AccessPolicy(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    allowed_roles = models.ManyToManyField(Group, blank=True)  # RBAC
    allowed_groups = models.ManyToManyField('IoTGroup', blank=True)
    conditions = models.JSONField(default=dict)  # ABAC: условия доступа

    def check_access(self, user, device, context=None):
        """ Проверка доступа по RBAC и ABAC """
        if context is None:
            context = {}
        user_roles = set(user.roles.values_list("name", flat=True))
        allowed_roles = set(self.allowed_roles.values_list("name", flat=True))
        if not user_roles.intersection(allowed_roles):
            log_user_to_device(
                device=device,
                user=user,
                status='Отказано',
                description=f'Отказано в доступе согласно политике [{self.name}] по причине: Несоответствие ролей'
            )
            return False

        for key, value in self.conditions.items():
            if key in context and context[key] != value:
                log_user_to_device(
                    device=device,
                    user=user,
                    status='Отказано',
                    description=f'Отказано в доступе согласно политике [{self.name}] по причине: Несоответствие контекста'
                )
                return False

        for key, value in self.conditions.items():
            if user.attributes.get(key) != value:
                log_user_to_device(
                    device=device,
                    user=user,
                    status='Отказано',
                    description=f'Отказано в доступе согласно политике [{self.name}] по причине: Несоответствие атрибутов'
                )
                return False
        log_user_to_device(
            device=device,
            user=user,
            status='Разрешено',
            description=f'Разрешено в доступе согласно политике [{self.name}]'
        )
        return True


class IoTGroup(models.Model):
    name = models.TextField()
    description = models.TextField()

    def __str__(self):
        return self.name


class IoTDevice(models.Model):
    device_name = models.CharField(max_length=100, null=True)
    device_type = models.CharField(max_length=100, null=True)
    uid = models.CharField(max_length=100, null=False, unique=True)
    registered_at = models.DateTimeField(auto_now_add=True, null=True)
    last_seen = models.DateTimeField(default=datetime.datetime.now(), null=True)
    groups = models.ManyToManyField('IoTGroup', related_name='iot_devices')
    description = models.TextField(null=True, default=None)

    class Meta:
        permissions = [
            ('can_view_device_information', 'can view device information'),
            ('can_send_device_information', 'can send device information'),
            ('can_disable_device', 'can disable device'),
        ]

    def __str__(self):
        return f'{self.device_name} [{self.device_type}]'


class UserLog(models.Model):
    status = models.CharField(max_length=16, db_index=True)
    user = models.ForeignKey('IoTUser', on_delete=models.DO_NOTHING)
    description = models.TextField()


class IoTDeviceLog(models.Model):
    status = models.CharField(max_length=16, db_index=True)
    device = models.ForeignKey('IoTDevice', on_delete=models.DO_NOTHING)
    description = models.TextField()


class UserToDeviceLog(models.Model):
    status = models.CharField(max_length=16, db_index=True)
    device = models.ForeignKey('IoTDevice', on_delete=models.DO_NOTHING)
    user = models.ForeignKey('IoTUser', on_delete=models.DO_NOTHING)
    at_time = models.DateTimeField(auto_now_add=True)
    description = models.TextField()


class IoTMessage(models.Model):
    device = models.ForeignKey(IoTDevice, on_delete=models.DO_NOTHING, db_index=True, related_name='device_msg')
    receive_time = models.DateTimeField(auto_now_add=True)
    topic = models.CharField(max_length=50, db_index=True)
    msg = models.TextField()

    def __str__(self):
        return f'msg: [{self.msg}] received at {self.receive_time} from topic: {self.topic}'
