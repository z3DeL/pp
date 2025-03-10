from django.http import HttpResponseServerError, HttpResponse
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

        try:
            # Пытаемся отрендерить шаблон ошибки
            html = render_to_string(template, {
                'request': request,
                'exception': str(exception)
            })
            return HttpResponse(html, status=status_code)
        except Exception as e:
            # Если не удалось отрендерить шаблон, возвращаем базовый HTML
            logger.error(f"Error rendering error template: {str(e)}", exc_info=True)
            return HttpResponseServerError("""
                <html>
                    <head>
                        <title>500 - Внутренняя ошибка сервера</title>
                        <style>
                            body { 
                                font-family: Arial, sans-serif; 
                                text-align: center; 
                                padding: 50px;
                                background-color: #f8f9fa;
                            }
                            h1 { 
                                color: #dc3545;
                                font-size: 3rem;
                                margin-bottom: 1rem;
                            }
                            p { 
                                color: #6c757d;
                                font-size: 1.2rem;
                                margin-bottom: 2rem;
                            }
                            .btn {
                                display: inline-block;
                                padding: 10px 20px;
                                background-color: #007bff;
                                color: white;
                                text-decoration: none;
                                border-radius: 5px;
                            }
                        </style>
                    </head>
                    <body>
                        <h1>500 - Внутренняя ошибка сервера</h1>
                        <p>Произошла ошибка при обработке вашего запроса.</p>
                        <p>Пожалуйста, попробуйте позже или обратитесь к администратору.</p>
                        <a href="/" class="btn">Вернуться на главную</a>
                    </body>
                </html>
            """) 