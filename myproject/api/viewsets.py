from django.db import models
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import IntegrityError
from ..models import User, Department, Application, Skill, UserSkill, Message, Review, Notification, Job
from ..serializers import (
    UserSerializer, DepartmentSerializer, ApplicationSerializer,
    SkillSerializer, UserSkillSerializer, MessageSerializer, ReviewSerializer,
    NotificationSerializer, JobSerializer
)
from ..exceptions import (
    PermissionError, ConflictError, ApplicationAlreadyExistsError, JobNotFoundError,
    InvalidApplicationStatusError
)
from .base import BaseModelViewSet
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class UserViewSet(BaseModelViewSet):
    """
    API для работы с пользователями.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
        return User.objects.all()

    @swagger_auto_schema(
        operation_description="Создать нового пользователя (регистрация)",
        operation_summary="Регистрация пользователя",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'email', 'password', 'role'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Имя пользователя'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description='Email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD, description='Пароль'),
                'role': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    enum=['student', 'employer', 'admin'],
                    description='Роль пользователя'
                )
            }
        ),
        responses={
            201: UserSerializer,
            400: "Ошибка валидации данных"
        }
    )
    def create(self, request, *args, **kwargs):
        """Создание нового пользователя (регистрация)"""
        return super().create(request, *args, **kwargs)
        
    @swagger_auto_schema(
        operation_description="Получить список всех пользователей",
        operation_summary="Список пользователей"
    )
    def list(self, request, *args, **kwargs):
        """Получение списка пользователей"""
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Получить информацию о пользователе",
        operation_summary="Информация о пользователе",
        responses={
            200: UserSerializer,
            404: "Пользователь не найден"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """Получение информации о пользователе"""
        return super().retrieve(request, *args, **kwargs)

    def get_permissions(self):
        if self.action in ['create']:
            return [permissions.AllowAny()]
        return super().get_permissions()

class DepartmentViewSet(BaseModelViewSet):
    """
    API для работы с отделами компании.
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Department.objects.none()
        return Department.objects.all()

    @swagger_auto_schema(
        operation_description="Создать новый отдел компании",
        operation_summary="Создать отдел",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name', 'description', 'location', 'contact_email'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Название отдела'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Описание отдела'),
                'location': openapi.Schema(type=openapi.TYPE_STRING, description='Местоположение'),
                'contact_email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description='Контактный email')
            }
        ),
        responses={
            201: DepartmentSerializer,
            400: "Ошибка валидации данных"
        }
    )
    def create(self, request, *args, **kwargs):
        """Создание нового отдела"""
        return super().create(request, *args, **kwargs)

class ApplicationViewSet(BaseModelViewSet):
    """
    API для работы с заявками на вакансии.
    """
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Application.objects.none()
        if self.request.user.role == 'employer':
            return Application.objects.filter(job__employer=self.request.user)
        return Application.objects.filter(applicant=self.request.user)

    @swagger_auto_schema(
        operation_description="Получить список заявок текущего пользователя. Для работодателей - заявки на их вакансии, для студентов - их собственные заявки.",
        operation_summary="Список заявок",
        responses={
            200: ApplicationSerializer(many=True)
        }
    )
    def list(self, request, *args, **kwargs):
        """Получение списка заявок"""
        return super().list(request, *args, **kwargs)
        
    @swagger_auto_schema(
        operation_description="Получить детали заявки",
        operation_summary="Детали заявки",
        responses={
            200: ApplicationSerializer,
            404: "Заявка не найдена"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """Получение деталей заявки"""
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Создать новую заявку на вакансию (доступно только для студентов)",
        operation_summary="Создать заявку",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['job', 'cover_letter', 'resume'],
            properties={
                'job': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID вакансии'),
                'cover_letter': openapi.Schema(type=openapi.TYPE_STRING, description='Сопроводительное письмо'),
                'resume': openapi.Schema(type=openapi.TYPE_FILE, description='Резюме (файл)')
            }
        ),
        responses={
            201: ApplicationSerializer,
            400: "Ошибка валидации данных",
            403: "У вас нет прав для создания заявки",
            409: "Вы уже подали заявку на эту вакансию"
        }
    )
    def create(self, request, *args, **kwargs):
        """Создание новой заявки на вакансию"""
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        try:
            # Проверяем, есть ли уже заявка от этого пользователя на эту вакансию
            existing_application = Application.objects.filter(
                job=serializer.validated_data['job'],
                applicant=self.request.user
            ).exists()
            
            if existing_application:
                raise ApplicationAlreadyExistsError()
            
            # Проверяем, является ли пользователь работодателем для этой вакансии
            if self.request.user == serializer.validated_data['job'].employer:
                raise PermissionError('Работодатель не может подавать заявку на свою вакансию')
            
            serializer.save(applicant=self.request.user)
            
        except IntegrityError:
            raise ApplicationAlreadyExistsError()

    @swagger_auto_schema(
        operation_description="Обновить статус заявки (доступно только работодателю вакансии)",
        operation_summary="Обновить статус заявки",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['status'],
            properties={
                'status': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['pending', 'accepted', 'rejected', 'withdrawn'],
                    description='Новый статус заявки'
                )
            }
        ),
        responses={
            200: "{'status': 'success'}",
            400: "Неверный статус заявки",
            403: "У вас нет прав для изменения статуса этой заявки",
            404: "Заявка не найдена"
        }
    )
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Обновление статуса заявки"""
        application = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Application.STATUS_CHOICES):
            raise InvalidApplicationStatusError()
        
        if request.user.role != 'employer' or application.job.employer != request.user:
            raise PermissionError(detail='У вас нет прав для изменения статуса этой заявки')
        
        application.status = new_status
        application.save()
        
        return Response({'status': 'success'})

class SkillViewSet(BaseModelViewSet):
    """
    API для работы с навыками.
    """
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Skill.objects.none()
        return Skill.objects.all()

    @swagger_auto_schema(
        operation_description="Получить список всех навыков",
        operation_summary="Список навыков"
    )
    def list(self, request, *args, **kwargs):
        """Получение списка навыков"""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Создать новый навык",
        operation_summary="Создать навык",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name', 'category'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Название навыка'),
                'category': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['technical', 'soft', 'language', 'other'],
                    description='Категория навыка'
                )
            }
        ),
        responses={
            201: SkillSerializer,
            400: "Ошибка валидации данных"
        }
    )
    def create(self, request, *args, **kwargs):
        """Создание нового навыка"""
        return super().create(request, *args, **kwargs)

class UserSkillViewSet(BaseModelViewSet):
    """
    API для работы с навыками пользователей.
    """
    queryset = UserSkill.objects.all()
    serializer_class = UserSkillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return UserSkill.objects.none()
        return UserSkill.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Получить список навыков текущего пользователя",
        operation_summary="Список навыков пользователя"
    )
    def list(self, request, *args, **kwargs):
        """Получение списка навыков пользователя"""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Добавить навык пользователю",
        operation_summary="Добавить навык пользователю",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['skill', 'level'],
            properties={
                'skill': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID навыка'),
                'level': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['beginner', 'intermediate', 'advanced'],
                    description='Уровень владения навыком'
                )
            }
        ),
        responses={
            201: UserSkillSerializer,
            400: "Ошибка валидации данных"
        }
    )
    def create(self, request, *args, **kwargs):
        """Добавление навыка пользователю"""
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class MessageViewSet(BaseModelViewSet):
    """
    API для работы с сообщениями.
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Message.objects.none()
        return Message.objects.filter(
            models.Q(sender=self.request.user) | 
            models.Q(receiver=self.request.user)
        )

    @swagger_auto_schema(
        operation_description="Получить список сообщений текущего пользователя (отправленных и полученных)",
        operation_summary="Список сообщений"
    )
    def list(self, request, *args, **kwargs):
        """Получение списка сообщений пользователя"""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Отправить новое сообщение",
        operation_summary="Отправить сообщение",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['receiver', 'content'],
            properties={
                'receiver': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID получателя'),
                'content': openapi.Schema(type=openapi.TYPE_STRING, description='Содержание сообщения'),
                'application': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID заявки (опционально)')
            }
        ),
        responses={
            201: MessageSerializer,
            400: "Ошибка валидации данных",
            404: "Получатель не найден"
        }
    )
    def create(self, request, *args, **kwargs):
        """Отправка нового сообщения"""
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

class ReviewViewSet(BaseModelViewSet):
    """
    API для работы с отзывами о вакансиях.
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Review.objects.none()
        return Review.objects.filter(
            models.Q(job__employer=self.request.user) |
            models.Q(reviewer=self.request.user)
        )

    @swagger_auto_schema(
        operation_description="Получить список отзывов (написанных пользователем или о его вакансиях)",
        operation_summary="Список отзывов"
    )
    def list(self, request, *args, **kwargs):
        """Получение списка отзывов"""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Создать новый отзыв о вакансии",
        operation_summary="Создать отзыв",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['job', 'rating', 'comment'],
            properties={
                'job': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID вакансии'),
                'rating': openapi.Schema(type=openapi.TYPE_INTEGER, description='Оценка (от 1 до 5)'),
                'comment': openapi.Schema(type=openapi.TYPE_STRING, description='Комментарий'),
                'is_anonymous': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Анонимный отзыв')
            }
        ),
        responses={
            201: ReviewSerializer,
            400: "Ошибка валидации данных",
            404: "Вакансия не найдена"
        }
    )
    def create(self, request, *args, **kwargs):
        """Создание нового отзыва"""
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)

class NotificationViewSet(BaseModelViewSet):
    """
    API для работы с уведомлениями.
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Получить список уведомлений текущего пользователя",
        operation_summary="Список уведомлений"
    )
    def list(self, request, *args, **kwargs):
        """Получение списка уведомлений"""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Отметить уведомление как прочитанное",
        operation_summary="Отметить как прочитанное",
        responses={
            200: "{'status': 'notification marked as read'}",
            403: "Недостаточно прав",
            404: "Уведомление не найдено"
        }
    )
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Отметка уведомления как прочитанного"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'notification marked as read'})

class JobViewSet(BaseModelViewSet):
    """
    API для работы с вакансиями.
    """
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Job.objects.none()
        return Job.objects.all()

    @swagger_auto_schema(
        operation_description="Создать новую вакансию (доступно только для работодателей)",
        operation_summary="Создать вакансию",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['title', 'description', 'department_id', 'job_type', 'deadline'],
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, description='Название вакансии'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Описание вакансии'),
                'department_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID отдела'),
                'job_type': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    enum=['internship', 'part_time', 'research', 'teaching'],
                    description='Тип вакансии'
                ),
                'requirements': openapi.Schema(type=openapi.TYPE_STRING, description='Требования к кандидатам'),
                'salary': openapi.Schema(type=openapi.TYPE_NUMBER, description='Зарплата'),
                'deadline': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description='Дедлайн подачи заявок')
            }
        ),
        responses={
            201: JobSerializer,
            400: "Ошибка валидации данных",
            403: "Только работодатели могут создавать вакансии"
        }
    )
    def create(self, request, *args, **kwargs):
        """Создание новой вакансии"""
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        if self.request.user.role != 'employer':
            raise PermissionError('Только работодатели могут создавать вакансии')
        serializer.save(employer=self.request.user)

    @swagger_auto_schema(
        operation_description="Обновить существующую вакансию (доступно только создателю вакансии)",
        operation_summary="Обновить вакансию",
        responses={
            200: JobSerializer,
            400: "Ошибка валидации данных",
            403: "Только работодатель может редактировать свою вакансию",
            404: "Вакансия не найдена"
        }
    )
    def update(self, request, *args, **kwargs):
        """Обновление вакансии"""
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        if self.request.user != self.get_object().employer:
            raise PermissionError('Только работодатель может редактировать свою вакансию')
        serializer.save()

    @swagger_auto_schema(
        operation_description="Удалить вакансию (доступно только создателю вакансии)",
        operation_summary="Удалить вакансию",
        responses={
            204: "Вакансия успешно удалена",
            403: "Только работодатель может удалять свою вакансию",
            404: "Вакансия не найдена"
        }
    )
    def destroy(self, request, *args, **kwargs):
        """Удаление вакансии"""
        return super().destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        if self.request.user != instance.employer:
            raise PermissionError('Только работодатель может удалять свою вакансию')
        instance.delete()

    @swagger_auto_schema(
        operation_description="Получить список заявок на вакансию (доступно только работодателю)",
        operation_summary="Заявки на вакансию",
        responses={
            200: ApplicationSerializer(many=True),
            403: "Только работодатель может просматривать заявки на свою вакансию",
            404: "Вакансия не найдена"
        }
    )
    @action(detail=True, methods=['get'])
    def applications(self, request, pk=None):
        """Получение списка заявок на вакансию"""
        job = self.get_object()
        if request.user != job.employer:
            raise PermissionError('Только работодатель может просматривать заявки на свою вакансию')
        
        applications = job.applications.all()
        serializer = ApplicationSerializer(applications, many=True)
        return Response(serializer.data) 