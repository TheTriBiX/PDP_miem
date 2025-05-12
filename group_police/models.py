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


class RBACPolicy(models.Model):
    name = models.CharField(max_length=64, verbose_name='Имя', db_comment='Имя политики')
    description = models.CharField(max_length=64, verbose_name='Описание', db_comment='Описание политики')
    action = models.CharField(choices=[('A', 'ALLOW'), ('D', 'DROP'), ('R', 'REDIRECT')],
                              verbose_name="Действие над запросом", max_length=1)
    hosts = models.TextField(verbose_name="Запросы от адресов")
    redirect_hosts = models.TextField(verbose_name="Перенаправлять на адреса")
    iot_groups = models.ManyToManyField('IoTGroup', verbose_name='Группы IoT-устройств')

    class Meta:
        db_table = 'RBACPolicy'
        verbose_name = 'Групповая политика'
        verbose_name_plural = 'Групповые политики'


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

    class Meta:
        # db_table = 'RBACPolicy'
        verbose_name = 'Группы IoT-устройств'
        verbose_name_plural = 'Группы IoT-устройств'

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
        verbose_name = 'IoT-устройство'
        verbose_name_plural = 'IoT-устройства'

    def __str__(self):
        return f'{self.device_name} [{self.device_type}]'


class UserLog(models.Model):
    status = models.CharField(max_length=16, db_index=True)
    user = models.ForeignKey('IoTUser', on_delete=models.DO_NOTHING)
    description = models.TextField()

    class Meta:
        verbose_name = 'События сгенерированные изменением групповых политик'
        verbose_name_plural = 'События сгенерированные изменением групповых политик'


class IoTDeviceLog(models.Model):
    status = models.CharField(max_length=16, db_index=True)
    device = models.ForeignKey('IoTDevice', on_delete=models.DO_NOTHING)
    description = models.TextField()

    class Meta:
        # db_table = 'RBACPolicy'
        verbose_name = 'События сгенерированные IoT-устройствами'
        verbose_name_plural = 'События сгенерированные IoT-устройствами'


class UserToDeviceLog(models.Model):
    status = models.CharField(max_length=16, db_index=True)
    device = models.ForeignKey('IoTDevice', on_delete=models.DO_NOTHING)
    user = models.ForeignKey('IoTUser', on_delete=models.DO_NOTHING)
    at_time = models.DateTimeField(auto_now_add=True)
    description = models.TextField()

    class Meta:
        verbose_name = 'События сгенерированные изменением групп IoT-устройств'
        verbose_name_plural = 'События сгенерированные изменением групп IoT-устройств'


class IoTMessage(models.Model):
    device = models.ForeignKey(IoTDevice, on_delete=models.DO_NOTHING, db_index=True, related_name='device_msg')
    receive_time = models.DateTimeField(auto_now_add=True)
    topic = models.CharField(max_length=50, db_index=True)
    msg = models.TextField()

    def __str__(self):
        return f'msg: [{self.msg}] received at {self.receive_time} from topic: {self.topic}'
