from django.core.exceptions import ValidationError
from django.utils import timezone
from ..models import Job, Application, User, Department
from ..exceptions import ValidationError as CustomValidationError

def validate_job_parameters(data):
    """
    Валидация параметров для создания/обновления вакансии
    """
    errors = {}
    
    # Проверка заголовка
    if 'title' in data:
        if len(data['title']) < 5:
            errors['title'] = {
                'message': 'Заголовок должен содержать минимум 5 символов',
                'current_value': data['title'],
                'suggestions': [
                    'Увеличьте длину заголовка',
                    'Добавьте более подробное описание должности'
                ]
            }
    
    # Проверка дедлайна
    if 'deadline' in data:
        try:
            deadline = timezone.datetime.strptime(data['deadline'], '%Y-%m-%d')
            if deadline.date() < timezone.now().date():
                errors['deadline'] = {
                    'message': 'Дедлайн не может быть в прошлом',
                    'current_value': data['deadline'],
                    'suggestions': [
                        'Установите будущую дату',
                        'Минимальный срок - завтрашний день'
                    ]
                }
        except ValueError:
            errors['deadline'] = {
                'message': 'Неверный формат даты',
                'current_value': data['deadline'],
                'suggestions': [
                    'Используйте формат YYYY-MM-DD',
                    'Пример: 2024-12-31'
                ]
            }
    
    # Проверка зарплаты
    if 'salary' in data:
        try:
            salary = float(data['salary'])
            if salary < 0:
                errors['salary'] = {
                    'message': 'Зарплата не может быть отрицательной',
                    'current_value': data['salary'],
                    'suggestions': [
                        'Укажите положительное значение',
                        'Если зарплата не указана, оставьте поле пустым'
                    ]
                }
        except ValueError:
            errors['salary'] = {
                'message': 'Неверный формат зарплаты',
                'current_value': data['salary'],
                'suggestions': [
                    'Используйте числовое значение',
                    'Можно использовать десятичные дроби'
                ]
            }
    
    if errors:
        raise CustomValidationError(detail=errors)

def validate_application_parameters(data, user):
    """
    Валидация параметров для создания заявки
    """
    errors = {}
    
    # Проверка вакансии
    if 'job' in data:
        try:
            job = Job.objects.get(id=data['job'])
            if job.deadline < timezone.now():
                errors['job'] = {
                    'message': 'Срок подачи заявки истек',
                    'current_value': job.id,
                    'suggestions': [
                        'Выберите актуальную вакансию',
                        'Проверьте дату публикации вакансии'
                    ]
                }
            elif Application.objects.filter(job=job, applicant=user).exists():
                errors['job'] = {
                    'message': 'Вы уже подали заявку на эту вакансию',
                    'current_value': job.id,
                    'suggestions': [
                        'Выберите другую вакансию',
                        'Проверьте список ваших заявок'
                    ]
                }
        except Job.DoesNotExist:
            errors['job'] = {
                'message': 'Вакансия не найдена',
                'current_value': data['job'],
                'suggestions': [
                    'Проверьте правильность ID вакансии',
                    'Выберите вакансию из списка доступных'
                ]
            }
    
    # Проверка сопроводительного письма
    if 'cover_letter' in data:
        if len(data['cover_letter']) < 100:
            errors['cover_letter'] = {
                'message': 'Сопроводительное письмо слишком короткое',
                'current_value': data['cover_letter'],
                'suggestions': [
                    'Добавьте больше информации о себе',
                    'Опишите свой опыт и навыки',
                    'Минимальная длина - 100 символов'
                ]
            }
    
    if errors:
        raise CustomValidationError(detail=errors)

def validate_user_parameters(data):
    """
    Валидация параметров для создания/обновления пользователя
    """
    errors = {}
    
    # Проверка email
    if 'email' in data:
        if User.objects.filter(email=data['email']).exists():
            errors['email'] = {
                'message': 'Этот email уже используется',
                'current_value': data['email'],
                'suggestions': [
                    'Используйте другой email',
                    'Восстановите доступ к существующему аккаунту'
                ]
            }
    
    # Проверка username
    if 'username' in data:
        if len(data['username']) < 3:
            errors['username'] = {
                'message': 'Имя пользователя слишком короткое',
                'current_value': data['username'],
                'suggestions': [
                    'Используйте минимум 3 символа',
                    'Можно использовать буквы, цифры и знаки подчеркивания'
                ]
            }
        elif User.objects.filter(username=data['username']).exists():
            errors['username'] = {
                'message': 'Это имя пользователя уже занято',
                'current_value': data['username'],
                'suggestions': [
                    'Выберите другое имя пользователя',
                    'Добавьте цифры или специальные символы'
                ]
            }
    
    # Проверка пароля
    if 'password' in data:
        if len(data['password']) < 8:
            errors['password'] = {
                'message': 'Пароль слишком короткий',
                'current_value': '********',
                'suggestions': [
                    'Используйте минимум 8 символов',
                    'Добавьте заглавные буквы, цифры и специальные символы'
                ]
            }
    
    if errors:
        raise CustomValidationError(detail=errors)

def validate_department_parameters(data):
    """
    Валидация параметров для создания/обновления отдела
    """
    errors = {}
    
    # Проверка названия
    if 'name' in data:
        if len(data['name']) < 3:
            errors['name'] = {
                'message': 'Название отдела слишком короткое',
                'current_value': data['name'],
                'suggestions': [
                    'Используйте минимум 3 символа',
                    'Добавьте более подробное название'
                ]
            }
        elif Department.objects.filter(name=data['name']).exists():
            errors['name'] = {
                'message': 'Отдел с таким названием уже существует',
                'current_value': data['name'],
                'suggestions': [
                    'Используйте другое название',
                    'Добавьте дополнительную информацию для различения'
                ]
            }
    
    # Проверка email
    if 'contact_email' in data:
        if Department.objects.filter(contact_email=data['contact_email']).exists():
            errors['contact_email'] = {
                'message': 'Этот email уже используется другим отделом',
                'current_value': data['contact_email'],
                'suggestions': [
                    'Используйте другой email',
                    'Проверьте правильность введенного email'
                ]
            }
    
    if errors:
        raise CustomValidationError(detail=errors) 