from base64 import b64encode
from io import BytesIO
from typing import Any

from django.contrib.auth import user_logged_in, authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django_otp.plugins.otp_totp.models import TOTPDevice
import qrcode
import qrcode.image.svg
from django_tables2 import SingleTableView

from group_police.models import IoTDevice, IoTUser, IoTMessage, AccessPolicy, UserToDeviceLog
from group_police.tables import DeviceTable
from mqtt_broker.devices import MQTT_LISTENER


def create_user(request, **kwargs):
    user = IoTUser.objects.get(
        username=request.POST.get('username'),
        password=request.POST.get('password'),
    )
    totp_device = TOTPDevice.objects.create(user=user)
    qr_code_img = qrcode.make(
        totp_device.config_url
    )
    buffer = BytesIO()
    qr_code_img.save(buffer)
    buffer.seek(0)
    encoded_img = b64encode(buffer.read()).decode()
    qr_code_data = f'data:image/png;base64,{encoded_img}'
    return render(request, 'register_confirm.html', {'qr_code': qr_code_data})


def confirm_register(request, *args, **kwargs):
    user = IoTUser.objects.get(
        username=request.POST.get('username'),
        password=request.POST.get('password'),
    )
    totp_device = TOTPDevice.objects.filter(user=user).first()
    if totp_device.verify_token(request.POST.get('otp_token')):
        login(request, user)
        return redirect('device_list')
    return redirect('login')


class RegisterView(View):
    def get(self, request, *args, **kwargs):
        context = {**request.GET}
        return render(request, 'register.html', context=context)


class IoTDeviceListView(LoginRequiredMixin, SingleTableView):
    table_class = DeviceTable
    template_name = 'main_page.html'
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        devices_qs = IoTDevice.objects.filter(
            groups__in=self.request.user.allowed_iot_groups.all(),
        ).values(
            'id',
            'device_name',
            'device_type',
            'last_seen',
        )
        return devices_qs


def logout_user(request):
    logout(request)
    return redirect("login")


class IoTDeviceView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        device = IoTDevice.objects.get(**kwargs)
        user = request.user
        if any(policy.check_access(user, device) for policy in AccessPolicy.objects.all()):
            permissions = user.groups.values_list('permissions__name', flat=True)
            context = {
                'permissions': permissions,
                'device': device,
                'device_msg': IoTMessage.objects.filter(
                    device=device,
                ).order_by(
                    'receive_time',
                )[:5:]
            }
            return render(request, 'device.html', context)
        else:
            context = {'error': True}
            return render(request, 'device.html', context)


class IoTDevicesAPIView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        msg = request.POST.get('device_message')
        device = IoTDevice.objects.get(uid=request.POST.get('device'))
        topic = f'/devices/{device.device_name}/data'
        try:
            MQTT_LISTENER.send_message(topic, msg)
            UserToDeviceLog.objects.create(
                user=request.user,
                device=device,
                status='Успешная отправка',
                description=f'successful send. msg: [{msg}] from user: [{request.user}] to device: [{device.device_name}]'
            )
        except Exception as e:
            UserToDeviceLog.objects.create(
                user=request.user,
                device=device,
                status='Неудачная отправка',
                description=f'unsuccessful send. msg: [{msg}] from user: [{request.user}] to device: [{device.device_name}]\n reason: [{e}]'
            )
        return redirect(reverse("device", kwargs={'pk': device.id}))
