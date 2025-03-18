Установка и запуск:
1. python 3.7+
2. Установить виртуальное окружение
3. pip install -r requirements.txt
4. python manage.py makemigrations
5. python manage.py createsuperuser
5. python manage.py migrate
6. python manage.py runserver
7. В браузере станет досутпна админская панель по адресу admin/. В ней нужно привязть устройство к раннее созданому пользователю для 2FA. После этого по адресу admin_2fa/ будет досутпна полная панель администратора.