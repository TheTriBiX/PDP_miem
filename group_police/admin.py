from django.contrib import admin
from django_otp.admin import OTPAdminSite
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_totp.admin import TOTPDeviceAdmin
from django.contrib.auth.models import Group

from group_police.models import IoTUser, AccessPolicy, IoTDevice, IoTGroup, UserLog, IoTDeviceLog, UserToDeviceLog, \
    RBACPolicy


class OTPAdmin(OTPAdminSite):
    pass

@admin.register(UserLog)
class UserLogAdmin(admin.ModelAdmin):
    list_display = ('status', 'user', 'description')

    class Meta:
        ordering = ('status', 'user',)

@admin.register(UserToDeviceLog)
class UserToDeviceAdmin(admin.ModelAdmin):
    list_display = ('status', 'user', 'device',)

    class Meta:
        ordering = ('status', 'user', 'device',)


@admin.register(IoTDeviceLog)
class IoTDeviceLogAdmin(admin.ModelAdmin):
    list_display = ('status', 'device',)

    class Meta:
        ordering = ('status', 'device',)

admin_site = OTPAdmin(name='OTPAdmin')

# admin_site.register(Group)
admin_site.register(RBACPolicy)
# admin_site.register(TOTPDevice, TOTPDeviceAdmin)
admin_site.register(IoTUser)
admin.register(IoTUser)
# admin_site.register(AccessPolicy)
admin_site.register(IoTGroup)
admin_site.register(IoTDevice)
admin_site.register(UserLog, UserLogAdmin)
admin_site.register(IoTDeviceLog)
admin_site.register(UserToDeviceLog, UserToDeviceAdmin)