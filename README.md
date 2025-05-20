# Проект вакансий УрФУ

## Настройка и запуск проекта

### Локальное развертывание

1. Клонировать репозиторий:
```bash
git clone https://github.com/yourusername/your-repo.git
cd your-repo
```

2. Создать и активировать виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate  # для Windows
```

3. Установить зависимости:
```bash
pip install -r requirements.txt
```

4. Создать файл .env на основе .env.example:
```bash
cp .env.example .env
# Отредактировать .env, указав реальные значения
```

5. Выполнить миграции и запустить сервер:
```bash
python manage.py migrate
python manage.py collectstatic
python manage.py runserver
```

### Запуск с Docker

1. Создать .env файл с переменными окружения:
```
YC_ACCESS_KEY_ID=your-access-key
YC_SECRET_ACCESS_KEY=your-secret-key
```

2. Запустить контейнеры:
```bash
docker-compose up -d --build
```

3. Приложение будет доступно по адресу http://localhost:8000

### Развертывание в Yandex Cloud Serverless Containers

1. Установить Yandex Cloud CLI:
```bash
curl https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash
```

2. Инициализировать Yandex Cloud CLI:
```bash
yc init
```

3. Создать Docker-образ и отправить его в Container Registry:
```bash
docker build -t cr.yandex/your-registry-id/myproject:latest .
docker push cr.yandex/your-registry-id/myproject:latest
```

4. Обновить serverless.yaml:
   - Указать правильный ID реестра вместо crp00000000000000000
   - Настроить переменные окружения

5. Развернуть приложение:
```bash
yc serverless container deploy --file serverless.yaml
```

## Переменные окружения

Проект использует следующие переменные окружения:

- `DEBUG` - режим отладки (True/False)
- `DB_ENGINE` - движок базы данных
- `DB_HOST` - хост базы данных (для PostgreSQL)
- `DB_NAME` - имя базы данных
- `DB_USER` - пользователь базы данных (для PostgreSQL)
- `DB_PASSWORD` - пароль для базы данных (для PostgreSQL)
- `DB_PORT` - порт базы данных (для PostgreSQL)
- `YC_ACCESS_KEY_ID` - ID ключа доступа для Yandex Cloud Object Storage
- `YC_SECRET_ACCESS_KEY` - секретный ключ для Yandex Cloud Object Storage

## Структура проекта

- `myproject/` - основной Django-проект
- `static/` - статические файлы
- `media/` - загружаемые пользователями файлы
- `staticfiles/` - собранные статические файлы (генерируется при collectstatic) 