from django.contrib import admin
from django.urls import path, re_path
from django_otp.views import login

from group_police.admin import admin_site
from group_police.views import RegisterView, create_user, confirm_register, IoTDeviceView, IoTDeviceListView, \
    IoTDevicesAPIView, logout_user

urlpatterns = [
    path('admin/', admin_site.urls),
    path('register/', RegisterView.as_view(), name='register'),
    path('api/register/', create_user, name='create_user'),
    path('login/', login, name='login'),
    path('logout/', logout_user, name='logout'),
    re_path(r'^api/register_confirm/$', confirm_register, name='register_confirm'),
    path('devices/', IoTDeviceListView.as_view(), name='device_list'),
    path('devices/<int:pk>/', IoTDeviceView.as_view(), name='device'),
    path('devices/<int:pk>/', IoTDeviceView.as_view(), name='device'),
    path('api/send_to_device/', IoTDevicesAPIView.as_view(), name='send_to_device'),
]
