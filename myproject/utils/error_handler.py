from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import (
    APIException, AuthenticationFailed, NotAuthenticated,
    PermissionDenied, NotFound, ValidationError as DRFValidationError
)
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.http import Http404, HttpResponse
from django.template.loader import render_to_string
from ..exceptions import (
    ValidationError, AuthenticationError, PermissionError,
    NotFoundError, ConflictError, ServerError, ApplicationAlreadyExistsError
)

def custom_authentication_failed_handler(exc, context):
    """
    Обработчик ошибок аутентификации
    """
    return Response({
        'error': {
            'code': 'authentication_error',
            'message': 'Требуется аутентификация',
            'details': str(exc),
            'suggestions': [
                'Проверьте правильность логина и пароля',
                'Убедитесь, что вы авторизованы в системе',
                'Попробуйте перезайти в систему'
            ]
        }
    }, status=status.HTTP_401_UNAUTHORIZED)

def custom_exception_handler(exc, context):
    """
    Кастомный обработчик исключений для API
    """
    print(f"Exception type: {type(exc)}")
    print(f"Exception: {exc}")
    print(f"Context: {context}")

    # Проверяем, что контекст существует и содержит request
    if not context or 'request' not in context:
        return Response({
            'error': {
                'code': 'server_error',
                'message': 'Внутренняя ошибка сервера',
                'details': str(exc)
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    request = context['request']
    # Проверяем, является ли запрос API запросом
    is_api_request = request.path.startswith('/api/') or 'application/json' in request.META.get('HTTP_ACCEPT', '')
    
    if not is_api_request:
        # Для веб-запросов возвращаем HTML страницу
        if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
            template = 'errors/401.html'
            status_code = 401
        elif isinstance(exc, PermissionDenied):
            template = 'errors/403.html'
            status_code = 403
        elif isinstance(exc, (NotFound, Http404)):
            template = 'errors/404.html'
            status_code = 404
        else:
            template = 'errors/500.html'
            status_code = 500
        
        try:
            html = render_to_string(template, {'exception': exc})
            return HttpResponse(html, status=status_code)
        except Exception as template_error:
            print(f"Error rendering template: {template_error}")
            # Продолжаем с JSON-ответом, если шаблон не может быть отрендерен
    
    # Далее - логика обработки исключений для API
    # Преобразуем стандартные исключения DRF в наши кастомные
    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        return Response({
            'error': {
                'code': 'authentication_error',
                'message': 'Требуется аутентификация',
                'details': str(exc),
                'suggestions': get_error_suggestions(exc, context)
            }
        }, status=status.HTTP_401_UNAUTHORIZED)
    elif isinstance(exc, PermissionDenied):
        return Response({
            'error': {
                'code': 'permission_error',
                'message': str(exc),
                'details': str(exc),
                'suggestions': get_error_suggestions(exc, context)
            }
        }, status=status.HTTP_403_FORBIDDEN)
    elif isinstance(exc, IntegrityError):
        return Response({
            'error': {
                'code': 'conflict',
                'message': str(exc),
                'details': str(exc),
                'suggestions': get_error_suggestions(exc, context)
            }
        }, status=status.HTTP_409_CONFLICT)
    elif isinstance(exc, (NotFound, Http404, NotFoundError)):
        return Response({
            'error': {
                'code': 'not_found',
                'message': str(exc),
                'details': str(exc),
                'suggestions': get_error_suggestions(exc, context)
            }
        }, status=status.HTTP_404_NOT_FOUND)
    elif isinstance(exc, (ValidationError, DjangoValidationError, DRFValidationError)):
        if hasattr(exc, 'detail'):
            details = exc.detail
        elif hasattr(exc, 'message_dict'):
            details = exc.message_dict
        else:
            details = str(exc)
        
        return Response({
            'error': {
                'code': 'validation_error',
                'message': 'Ошибка валидации данных',
                'details': details,
                'suggestions': get_error_suggestions(exc, context)
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Для всех остальных исключений
    response = exception_handler(exc, context)
    if response is not None:
        # Преобразуем ответ в наш формат
        if hasattr(exc, 'detail'):
            details = exc.detail
        else:
            details = str(exc)
        
        error_code = 'validation_error' if isinstance(exc, (ValidationError, DRFValidationError)) else getattr(exc, 'default_code', 'error')
        status_code = response.status_code
        
        return Response({
            'error': {
                'code': error_code,
                'message': str(exc),
                'details': details,
                'suggestions': get_error_suggestions(exc, context)
            }
        }, status=status_code)
    
    return Response({
        'error': {
            'code': 'server_error',
            'message': 'Внутренняя ошибка сервера',
            'details': str(exc)
        }
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def get_error_suggestions(exc, context=None):
    """
    Возвращает список предложений в зависимости от типа ошибки и метода запроса
    """
    request = None
    view_class = None
    action = None
    
    # Получаем информацию о запросе и представлении
    if context and 'request' in context:
        request = context['request']
        if 'view' in context:
            view_class = context['view'].__class__.__name__
            action = getattr(context['view'], 'action', None)
    
    method = request.method if request else None
    path = request.path if request else None
    
    # Идентифицируем ресурс по пути
    resource_type = 'unknown'
    if path:
        if '/api/users' in path:
            resource_type = 'user'
        elif '/api/jobs' in path:
            resource_type = 'job'
        elif '/api/applications' in path:
            resource_type = 'application'
        elif '/api/departments' in path:
            resource_type = 'department'
        elif '/api/skills' in path:
            resource_type = 'skill'
        elif '/api/user-skills' in path:
            resource_type = 'user_skill'
        elif '/api/messages' in path:
            resource_type = 'message'
        elif '/api/reviews' in path:
            resource_type = 'review'
        elif '/api/notifications' in path:
            resource_type = 'notification'
    
    # Базовые предложения по типу исключения
    if isinstance(exc, (ValidationError, DRFValidationError)):
        suggestions = []
        if hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                for field, errors in exc.detail.items():
                    if isinstance(errors, list):
                        for error in errors:
                            # Предложения в зависимости от ресурса и метода
                            # ПОЛЬЗОВАТЕЛИ
                            if resource_type == 'user':
                                if method == 'POST':  # Создание пользователя
                                    if field == 'username':
                                        if error.code == 'required':
                                            suggestions.append('Укажите имя пользователя для регистрации')
                                        elif error.code == 'unique':
                                            suggestions.append('Это имя пользователя уже занято. Выберите другое')
                                    elif field == 'email':
                                        if error.code == 'required':
                                            suggestions.append('Укажите email для регистрации')
                                        elif error.code == 'invalid':
                                            suggestions.append('Укажите корректный email (например, example@domain.com)')
                                        elif error.code == 'unique':
                                            suggestions.append('Пользователь с таким email уже зарегистрирован')
                                    elif field == 'password':
                                        if error.code == 'required':
                                            suggestions.append('Укажите пароль для регистрации')
                                        elif error.code == 'min_length':
                                            suggestions.append('Пароль должен содержать не менее 8 символов')
                                    elif field == 'role':
                                        if error.code == 'required':
                                            suggestions.append('Выберите роль: student, employer или admin')
                                        elif error.code == 'invalid_choice':
                                            suggestions.append('Выберите одну из доступных ролей: student, employer или admin')
                                elif method == 'PUT' or method == 'PATCH':  # Обновление пользователя
                                    if field == 'email':
                                        if error.code == 'unique':
                                            suggestions.append('Этот email уже используется другим пользователем')
                            
                            # ВАКАНСИИ
                            elif resource_type == 'job':
                                if method == 'POST':  # Создание вакансии
                                    if field == 'title':
                                        if error.code == 'required':
                                            suggestions.append('Укажите название вакансии')
                                        elif error.code == 'blank':
                                            suggestions.append('Название вакансии не может быть пустым')
                                    elif field == 'description':
                                        if error.code == 'required':
                                            suggestions.append('Добавьте описание вакансии')
                                    elif field == 'department_id':
                                        if error.code == 'required':
                                            suggestions.append('Выберите отдел для вакансии')
                                        elif error.code == 'does_not_exist':
                                            suggestions.append('Указанный отдел не существует. Выберите существующий отдел')
                                    elif field == 'job_type':
                                        if error.code == 'required':
                                            suggestions.append('Выберите тип вакансии: internship, part_time, research или teaching')
                                        elif error.code == 'invalid_choice':
                                            suggestions.append('Выберите один из доступных типов: internship, part_time, research или teaching')
                                    elif field == 'deadline':
                                        if error.code == 'required':
                                            suggestions.append('Укажите дедлайн для подачи заявок в формате ГГГГ-ММ-ДД')
                                        elif error.code == 'invalid':
                                            suggestions.append('Укажите корректную дату в формате ГГГГ-ММ-ДД')
                                elif method == 'PUT' or method == 'PATCH':  # Обновление вакансии
                                    if field == 'department_id':
                                        if error.code == 'does_not_exist':
                                            suggestions.append('Указанный отдел не существует. Выберите существующий отдел')
                            
                            # ЗАЯВКИ
                            elif resource_type == 'application':
                                if method == 'POST':  # Создание заявки
                                    if field == 'job':
                                        if error.code == 'required':
                                            suggestions.append('Укажите ID вакансии для подачи заявки')
                                        elif error.code == 'does_not_exist':
                                            suggestions.append('Указанная вакансия не существует')
                                    elif field == 'cover_letter':
                                        if error.code == 'required':
                                            suggestions.append('Добавьте сопроводительное письмо для заявки')
                                        elif error.code == 'blank':
                                            suggestions.append('Сопроводительное письмо не может быть пустым')
                                    elif field == 'resume':
                                        if error.code == 'required':
                                            suggestions.append('Загрузите ваше резюме (CV) в формате PDF')
                                        elif error.code == 'invalid':
                                            suggestions.append('Загрузите файл резюме в поддерживаемом формате (PDF, DOC, DOCX)')
                                elif method == 'PATCH':  # Обновление статуса заявки
                                    if field == 'status':
                                        if error.code == 'invalid_choice':
                                            suggestions.append('Выберите один из допустимых статусов: pending, accepted, rejected, withdrawn')
                            
                            # ОТДЕЛЫ
                            elif resource_type == 'department':
                                if method == 'POST':  # Создание отдела
                                    if field == 'name':
                                        if error.code == 'required':
                                            suggestions.append('Укажите название отдела')
                                        elif error.code == 'unique':
                                            suggestions.append('Отдел с таким названием уже существует')
                                    elif field == 'contact_email':
                                        if error.code == 'invalid':
                                            suggestions.append('Укажите корректный email контактного лица')
                                elif method == 'PUT' or method == 'PATCH':  # Обновление отдела
                                    if field == 'name' and error.code == 'unique':
                                        suggestions.append('Отдел с таким названием уже существует. Выберите другое название')
                            
                            # НАВЫКИ
                            elif resource_type == 'skill':
                                if method == 'POST':  # Создание навыка
                                    if field == 'name':
                                        if error.code == 'required':
                                            suggestions.append('Укажите название навыка')
                                        elif error.code == 'unique':
                                            suggestions.append('Навык с таким названием уже существует')
                                    elif field == 'category':
                                        if error.code == 'required':
                                            suggestions.append('Выберите категорию навыка: technical, soft, language или other')
                                        elif error.code == 'invalid_choice':
                                            suggestions.append('Выберите одну из доступных категорий: technical, soft, language или other')
                            
                            # НАВЫКИ ПОЛЬЗОВАТЕЛЯ
                            elif resource_type == 'user_skill':
                                if method == 'POST':  # Добавление навыка пользователю
                                    if field == 'skill':
                                        if error.code == 'required':
                                            suggestions.append('Выберите навык из списка доступных')
                                        elif error.code == 'does_not_exist':
                                            suggestions.append('Указанный навык не существует')
                                    elif field == 'level':
                                        if error.code == 'required':
                                            suggestions.append('Укажите уровень владения навыком: beginner, intermediate или advanced')
                                        elif error.code == 'invalid_choice':
                                            suggestions.append('Выберите один из доступных уровней: beginner, intermediate или advanced')
                                elif method == 'PUT' or method == 'PATCH':  # Обновление навыка пользователя
                                    if field == 'level' and error.code == 'invalid_choice':
                                        suggestions.append('Выберите один из доступных уровней: beginner, intermediate или advanced')
                            
                            # СООБЩЕНИЯ
                            elif resource_type == 'message':
                                if method == 'POST':  # Отправка сообщения
                                    if field == 'receiver':
                                        if error.code == 'required':
                                            suggestions.append('Укажите получателя сообщения')
                                        elif error.code == 'does_not_exist':
                                            suggestions.append('Указанный получатель не существует')
                                    elif field == 'content':
                                        if error.code == 'required':
                                            suggestions.append('Напишите текст сообщения')
                                        elif error.code == 'blank':
                                            suggestions.append('Сообщение не может быть пустым')
                            
                            # ОТЗЫВЫ
                            elif resource_type == 'review':
                                if method == 'POST':  # Создание отзыва
                                    if field == 'job':
                                        if error.code == 'required':
                                            suggestions.append('Укажите вакансию для отзыва')
                                        elif error.code == 'does_not_exist':
                                            suggestions.append('Указанная вакансия не существует')
                                    elif field == 'rating':
                                        if error.code == 'required':
                                            suggestions.append('Укажите рейтинг от 1 до 5')
                                        elif error.code == 'min_value' or error.code == 'max_value':
                                            suggestions.append('Рейтинг должен быть от 1 до 5')
                                    elif field == 'comment':
                                        if error.code == 'required':
                                            suggestions.append('Напишите комментарий к отзыву')
                                        elif error.code == 'blank':
                                            suggestions.append('Комментарий не может быть пустым')
                            
                            # УВЕДОМЛЕНИЯ
                            elif resource_type == 'notification':
                                if method == 'PATCH':  # Обновление уведомления
                                    if field == 'is_read' and error.code == 'invalid':
                                        suggestions.append('Указывайте true или false для статуса прочтения')
                            
                            # Если нет специфичных предложений, используем общие
                            if not suggestions:
                                if error.code == 'required':
                                    suggestions.append(f'Поле "{field}" является обязательным. Пожалуйста, заполните его.')
                                elif error.code == 'blank':
                                    suggestions.append(f'Поле "{field}" не может быть пустым.')
                                elif error.code == 'invalid':
                                    suggestions.append(f'Некорректное значение в поле "{field}". Проверьте формат данных.')
                                elif error.code == 'incorrect_type':
                                    suggestions.append(f'Поле "{field}" имеет неверный тип данных. Проверьте формат.')
                                elif error.code == 'max_length':
                                    suggestions.append(f'Значение в поле "{field}" слишком длинное. Уменьшите количество символов.')
                                elif error.code == 'min_length':
                                    suggestions.append(f'Значение в поле "{field}" слишком короткое. Увеличьте количество символов.')
                                elif error.code == 'unique':
                                    suggestions.append(f'Значение в поле "{field}" уже существует. Выберите другое значение.')
                                else:
                                    suggestions.append(f'Ошибка в поле "{field}": {error}')
                    else:
                        suggestions.append(f'Ошибка в поле "{field}": {errors}')
            else:
                suggestions.append(str(exc.detail))
        
        # Если нет предложений, добавляем общие
        if not suggestions:
            # Общие предложения в зависимости от метода
            if method == 'POST':
                suggestions.extend([
                    'Проверьте правильность всех полей перед созданием ресурса',
                    'Убедитесь, что все обязательные поля заполнены',
                    'Проверьте формат данных в полях'
                ])
            elif method == 'PUT' or method == 'PATCH':
                suggestions.extend([
                    'Проверьте правильность всех обновляемых полей',
                    'Убедитесь, что формат данных соответствует требованиям',
                    'Некоторые поля могут быть только для чтения и не подлежат изменению'
                ])
            else:
                suggestions.extend([
                    'Проверьте правильность введенных данных',
                    'Убедитесь, что все обязательные поля заполнены',
                    'Проверьте формат данных'
                ])
        
        return suggestions
    
    # Аутентификация
    elif isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        if path and 'token' in path:
            return [
                'Проверьте правильность логина и пароля',
                'Убедитесь, что учетная запись активирована',
                'Для получения токена используйте правильные учетные данные'
            ]
        return [
            'Проверьте правильность логина и пароля',
            'Убедитесь, что вы авторизованы в системе',
            'Попробуйте перезайти в систему'
        ]
    
    # Права доступа
    elif isinstance(exc, (PermissionDenied, PermissionError)):
        if resource_type == 'job' and method == 'POST':
            return [
                'Только работодатели могут создавать вакансии',
                'Перейдите в аккаунт работодателя для создания вакансии',
                'Обратитесь к администратору для получения прав работодателя'
            ]
        elif resource_type == 'job' and (method == 'PUT' or method == 'PATCH' or method == 'DELETE'):
            return [
                'Вы можете редактировать только свои вакансии',
                'Только владелец вакансии может ее изменять или удалять',
                'Обратитесь к владельцу вакансии или администратору'
            ]
        elif resource_type == 'application' and method == 'POST':
            return [
                'Только студенты могут подавать заявки на вакансии',
                'Перейдите в аккаунт студента для подачи заявки',
                'Работодатели не могут подавать заявки на вакансии'
            ]
        elif resource_type == 'application' and (method == 'PUT' or method == 'PATCH'):
            return [
                'Только владелец заявки или работодатель могут изменять статус заявки',
                'Вы можете управлять только своими заявками или заявками на ваши вакансии',
                'Обратитесь к администратору, если вам нужен доступ к этой заявке'
            ]
        else:
            return [
                'Убедитесь, что у вас есть необходимые права',
                'Обратитесь к администратору для получения доступа',
                'Проверьте роль пользователя в системе'
            ]
    
    # Ресурс не найден
    elif isinstance(exc, (NotFound, Http404, NotFoundError)):
        if resource_type == 'job':
            return [
                'Указанная вакансия не найдена или была удалена',
                'Проверьте корректность ID вакансии',
                'Возможно, вакансия была архивирована или срок её действия истек'
            ]
        elif resource_type == 'user':
            return [
                'Указанный пользователь не найден',
                'Проверьте корректность ID пользователя',
                'Возможно, пользователь был удален или деактивирован'
            ]
        elif resource_type == 'application':
            return [
                'Указанная заявка не найдена',
                'Проверьте корректность ID заявки',
                'Возможно, заявка была удалена или вы не имеете к ней доступа'
            ]
        else:
            return [
                'Проверьте правильность URL',
                'Убедитесь, что запрашиваемый ресурс существует',
                'Попробуйте обновить страницу'
            ]
    
    # Ошибки целостности данных
    elif isinstance(exc, (IntegrityError, ConflictError, ApplicationAlreadyExistsError)):
        if resource_type == 'application' and method == 'POST':
            return [
                'Вы уже подали заявку на эту вакансию',
                'Один пользователь может подать только одну заявку на вакансию',
                'Вы можете отредактировать существующую заявку вместо создания новой'
            ]
        elif resource_type == 'user' and method == 'POST':
            return [
                'Пользователь с таким именем или email уже существует',
                'Выберите другое имя пользователя или email',
                'Если это ваш аккаунт, попробуйте восстановить пароль'
            ]
        else:
            return [
                'Проверьте уникальность данных',
                'Убедитесь, что ресурс с такими параметрами не существует',
                'Попробуйте использовать другие значения для уникальных полей'
            ]
    
    # Общие предложения для остальных ошибок
    return [
        'Попробуйте повторить запрос позже',
        'Обратитесь в службу поддержки',
        'Проверьте корректность запроса'
    ] 