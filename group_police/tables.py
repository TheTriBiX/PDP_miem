import django_tables2 as tables
from django.urls import reverse
from django.utils.html import format_html


class DeviceTable(tables.Table):
    id = tables.Column(
        orderable=False,
        visible=False,
        attrs={
            'tr': {
                "class": "device-button",
                "device-id": lambda record: f"{record['id']}",
            },
        }
    )
    device_name = tables.Column(
        orderable=False,
        verbose_name='Имя устройства',
        attrs={
            'td': {
                "class": "device-button",
                "device-id": lambda record: f"{record['id']}",
            },
        }
    )
    device_type = tables.Column(
        orderable=False,
        verbose_name='Тип устройства',
        attrs={
            'td': {
                "class": "device-button",
                "device-id": lambda record: f"{record['id']}",
            },
        }
    )
    last_seen = tables.Column(
        orderable=False,
        verbose_name='Последняя активность',
        attrs={
            'td': {
                "class": "device-button",
                "device-id": lambda record: f"{record['id']}",
            },
        }
    )

    def render_device_name(self, record):
        link = reverse('device', kwargs={"pk": record['id']})
        record_link = f'<div><a href="{link}">' + record["device_name"] + '</a></div>'
        return format_html(record_link)

    class Meta:
        template_name = "django_tables2/bootstrap5.html"