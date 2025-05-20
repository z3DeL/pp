#!/bin/bash

# Ждем 2 секунды перед запуском, чтобы убедиться, что сервисы запустились
sleep 2

# Создаем директории для статических файлов, если их нет
mkdir -p /app/staticfiles
mkdir -p /app/media

# Применяем миграции
python manage.py migrate

# Собираем статические файлы
python manage.py collectstatic --noinput

# Создаем суперпользователя (если он не существует)
echo "Создание администратора..."
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
DJANGO_SUPERUSER_USERNAME = '${DJANGO_SUPERUSER_USERNAME:-admin}';
DJANGO_SUPERUSER_EMAIL = '${DJANGO_SUPERUSER_EMAIL:-admin@example.com}';
DJANGO_SUPERUSER_PASSWORD = '${DJANGO_SUPERUSER_PASSWORD:-admin12345}';
if not User.objects.filter(username=DJANGO_SUPERUSER_USERNAME).exists():
    User.objects.create_superuser(DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD);
    print(f'Суперпользователь {DJANGO_SUPERUSER_USERNAME} создан');
else:
    print(f'Суперпользователь {DJANGO_SUPERUSER_USERNAME} уже существует');
"

# Запускаем сервер Django
python manage.py runserver 0.0.0.0:8080 