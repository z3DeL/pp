from rest_framework import viewsets
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class BaseModelViewSet(viewsets.ModelViewSet):
    """
    Базовый класс для всех ViewSet с улучшенной документацией Swagger
    """
    
    @swagger_auto_schema(
        operation_description="Получить список объектов",
        operation_summary="Список объектов"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Получить детальную информацию об объекте",
        operation_summary="Детали объекта",
        responses={404: "Объект не найден"}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Создать новый объект",
        operation_summary="Создать объект",
        responses={
            201: "Объект успешно создан",
            400: "Ошибка валидации данных",
            403: "Недостаточно прав для создания объекта"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Полное обновление объекта",
        operation_summary="Обновить объект",
        responses={
            200: "Объект успешно обновлен",
            400: "Ошибка валидации данных",
            403: "Недостаточно прав для обновления объекта",
            404: "Объект не найден"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Частичное обновление объекта",
        operation_summary="Частично обновить объект",
        responses={
            200: "Объект успешно обновлен",
            400: "Ошибка валидации данных",
            403: "Недостаточно прав для обновления объекта",
            404: "Объект не найден"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Удалить объект",
        operation_summary="Удалить объект",
        responses={
            204: "Объект успешно удален",
            403: "Недостаточно прав для удаления объекта",
            404: "Объект не найден"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs) 