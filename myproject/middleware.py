from django.http import HttpResponseServerError, HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.conf import settings
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
import logging

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        # Логируем ошибку
        logger.error(f"Error occurred: {str(exception)}", exc_info=True)
        
        # Определяем тип ошибки и соответствующий шаблон
        if isinstance(exception, NotAuthenticated):
            status_code = 401
            template = 'errors/401.html'
        elif isinstance(exception, PermissionDenied):
            status_code = 403
            template = 'errors/403.html'
        elif hasattr(exception, 'status_code'):
            status_code = exception.status_code
            template = f'errors/{status_code}.html'
        else:
            status_code = 500
            template = 'errors/500.html'

        # Проверяем, является ли запрос API запросом
        is_api_request = request.path.startswith('/api/') or 'application/json' in request.META.get('HTTP_ACCEPT', '')
        
        if is_api_request:
            # Для API запросов возвращаем JSON
            return JsonResponse({
                'error': {
                    'code': f'error_{status_code}',
                    'message': str(exception),
                    'details': str(exception)
                }
            }, status=status_code)
        else:
            # Для веб-запросов возвращаем HTML
            return HttpResponse(
                render_to_string(template, {'exception': exception}),
                status=status_code
            ) 