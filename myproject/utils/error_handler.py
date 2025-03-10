from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import (
    APIException, AuthenticationFailed, NotAuthenticated,
    PermissionDenied, NotFound, ValidationError as DRFValidationError
)
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.http import Http404
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

    # Преобразуем стандартные исключения DRF в наши кастомные
    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
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
    elif isinstance(exc, PermissionDenied):
        return Response({
            'error': {
                'code': 'permission_error',
                'message': str(exc),
                'details': str(exc),
                'suggestions': [
                    'Убедитесь, что у вас есть необходимые права',
                    'Обратитесь к администратору для получения доступа',
                    'Проверьте роль пользователя в системе'
                ]
            }
        }, status=status.HTTP_403_FORBIDDEN)
    elif isinstance(exc, IntegrityError):
        return Response({
            'error': {
                'code': 'conflict',
                'message': str(exc),
                'details': str(exc),
                'suggestions': [
                    'Проверьте уникальность данных',
                    'Убедитесь, что ресурс не существует',
                    'Попробуйте использовать другой идентификатор'
                ]
            }
        }, status=status.HTTP_409_CONFLICT)
    elif isinstance(exc, (NotFound, Http404, NotFoundError)):
        return Response({
            'error': {
                'code': 'not_found',
                'message': str(exc),
                'details': str(exc),
                'suggestions': [
                    'Проверьте правильность URL',
                    'Убедитесь, что запрашиваемый ресурс существует',
                    'Попробуйте обновить страницу'
                ]
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
                'suggestions': [
                    'Проверьте правильность введенных данных',
                    'Убедитесь, что все обязательные поля заполнены',
                    'Проверьте формат данных'
                ]
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
                'suggestions': get_error_suggestions(exc)
            }
        }, status=status_code)
    
    return Response({
        'error': {
            'code': 'server_error',
            'message': 'Внутренняя ошибка сервера',
            'details': str(exc)
        }
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def get_error_suggestions(exc):
    """
    Возвращает список предложений в зависимости от типа ошибки
    """
    if isinstance(exc, (ValidationError, DRFValidationError)):
        return [
            'Проверьте правильность введенных данных',
            'Убедитесь, что все обязательные поля заполнены',
            'Проверьте формат данных'
        ]
    elif isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        return [
            'Проверьте правильность логина и пароля',
            'Убедитесь, что вы авторизованы в системе',
            'Попробуйте перезайти в систему'
        ]
    elif isinstance(exc, (PermissionDenied, PermissionError)):
        return [
            'Убедитесь, что у вас есть необходимые права',
            'Обратитесь к администратору для получения доступа',
            'Проверьте роль пользователя в системе'
        ]
    elif isinstance(exc, (NotFound, Http404, NotFoundError)):
        return [
            'Проверьте правильность URL',
            'Убедитесь, что запрашиваемый ресурс существует',
            'Попробуйте обновить страницу'
        ]
    elif isinstance(exc, (IntegrityError, ConflictError, ApplicationAlreadyExistsError)):
        return [
            'Проверьте уникальность данных',
            'Убедитесь, что ресурс не существует',
            'Попробуйте использовать другой идентификатор'
        ]
    return [
        'Попробуйте повторить запрос позже',
        'Обратитесь в службу поддержки',
        'Проверьте корректность запроса'
    ] 