from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Job, Department, Skill, Application, UserSkill, JobSkill, User, Message, Review, Notification, Favorite
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.exceptions import NotAuthenticated, ValidationError, PermissionDenied, NotFound
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .forms import ApplicationForm, UserRegistrationForm
from rest_framework.response import Response
from .serializers import (
    ApplicationSerializer, UserSerializer,
    SkillSerializer, UserSkillSerializer,
    MessageSerializer, ReviewSerializer, NotificationSerializer,
    DepartmentSerializer, JobSerializer
)
from rest_framework import viewsets, status
from rest_framework.decorators import action
from .exceptions import (
    PermissionError, NotFoundError,
    ConflictError, ServerError, JobNotFoundError,
    ApplicationNotFoundError, UserNotFoundError,
    DepartmentNotFoundError, InvalidApplicationStatusError,
    ApplicationAlreadyExistsError, JobDeadlineExpiredError,
    InvalidFileTypeError, FileTooLargeError, ValidationError
)
from django.db import IntegrityError
from django.http import Http404
from django.db.models import Q
from .utils.validators import (
    validate_job_parameters,
    validate_application_parameters,
    validate_user_parameters,
    validate_department_parameters
)
from django.urls import reverse
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt, requires_csrf_token
import json
from django.http import HttpResponseServerError

# API Views
@swagger_auto_schema(
    method='get',
    operation_description="Получить список всех вакансий",
    manual_parameters=[
        openapi.Parameter('job_type', openapi.IN_QUERY, description="Тип вакансии", type=openapi.TYPE_STRING),
        openapi.Parameter('department', openapi.IN_QUERY, description="ID отдела", type=openapi.TYPE_INTEGER),
        openapi.Parameter('format', openapi.IN_QUERY, description="Формат ответа (html или json)", type=openapi.TYPE_STRING),
    ]
)
@api_view(['GET'])
@permission_classes([AllowAny])
def job_list(request):
    queryset = Job.objects.filter(is_active=True)
    
    job_type = request.GET.get('job_type')
    department = request.GET.get('department')
    format = request.GET.get('format', 'html')
    
    if job_type:
        queryset = queryset.filter(job_type=job_type)
    if department:
        queryset = queryset.filter(department_id=department)
    
    if format == 'json':
        return Response({
            'jobs': [
                {
                    'id': job.id,
                    'title': job.title,
                    'description': job.description,
                    'department': job.department.name,
                    'job_type': job.get_job_type_display(),
                    'salary': job.salary,
                    'deadline': job.deadline,
                    'created_at': job.created_at
                }
                for job in queryset
            ]
        })
    
    departments = Department.objects.all()
    return render(request, 'jobs/job_list.html', {
        'jobs': queryset,
        'departments': departments
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_detail(request, job_id):
    try:
        job = Job.objects.get(id=job_id)
        if request.accepted_renderer.format == 'json':
            return Response({
                'id': job.id,
                'title': job.title,
                'description': job.description,
                'department': job.department.name,
                'job_type': job.get_job_type_display(),
                'salary': job.salary,
                'deadline': job.deadline,
                'created_at': job.created_at
            })
        return render(request, 'jobs/job_detail.html', {'job': job})
    except Job.DoesNotExist:
        if request.accepted_renderer.format == 'json':
            raise NotFoundError(detail='Вакансия не найдена')
        raise Http404('Вакансия не найдена')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_favorites(request):
    jobs = Job.objects.filter(favorites=request.user)
    return Response({
        'jobs': [
            {
                'id': job.id,
                'title': job.title,
                'description': job.description,
                'department': job.department.name,
                'job_type': job.get_job_type_display(),
                'salary': job.salary,
                'deadline': job.deadline,
                'created_at': job.created_at
            }
            for job in jobs
        ]
    })

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def api_applications(request):
    if not request.user.is_authenticated:
        raise NotAuthenticated()
    
    if request.method == 'GET':
        if request.user.role == 'employer':
            applications = Application.objects.filter(job__employer=request.user)
        else:
            applications = Application.objects.filter(applicant=request.user)
        
        serializer = ApplicationSerializer(applications, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        try:
            job_id = request.data.get('job')
            if not job_id:
                raise ValidationError(detail={'job': 'Обязательное поле'})
            
            try:
                job = Job.objects.get(id=job_id)
            except Job.DoesNotExist:
                raise NotFound('Вакансия не найдена')
            
            if job.employer == request.user:
                raise PermissionDenied('Вы не можете подать заявку на свою вакансию')
            
            if Application.objects.filter(job=job, applicant=request.user).exists():
                raise IntegrityError('Вы уже подали заявку на эту вакансию')
            
            serializer = ApplicationSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(applicant=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            raise ValidationError(detail=serializer.errors)
            
        except ValidationError as e:
            raise e
        except IntegrityError as e:
            raise e
        except PermissionDenied as e:
            raise e
        except NotFound as e:
            raise e
        except Exception as e:
            raise e

# Web Views
def home(request):
    jobs = Job.objects.filter(is_active=True).order_by('-created_at')[:5]
    return render(request, 'home.html', {'jobs': jobs})

@login_required
def job_list(request):
    """Список всех вакансий"""
    jobs = Job.objects.all().order_by('-created_at')
    return render(request, 'jobs/job_list.html', {'jobs': jobs})

@login_required
def job_create(request):
    """Создание новой вакансии"""
    if request.user.role != 'employer':
        raise PermissionDenied("Только работодатели могут создавать вакансии")
    
    if request.method == 'POST':
        serializer = JobSerializer(data=request.POST)
        if serializer.is_valid():
            job = serializer.save(employer=request.user)
            messages.success(request, 'Вакансия успешно создана')
            return redirect('job_detail', job_id=job.id)
        else:
            messages.error(request, 'Ошибка при создании вакансии')
    else:
        serializer = JobSerializer()
    
    departments = Department.objects.all()
    skills = Skill.objects.all()
    job_types = Job.JOB_TYPE_CHOICES
    
    return render(request, 'jobs/job_form.html', {
        'serializer': serializer,
        'departments': departments,
        'skills': skills,
        'job_types': job_types
    })

@login_required
def job_edit(request, job_id):
    """Редактирование вакансии"""
    job = get_object_or_404(Job, id=job_id)
    if request.user != job.employer:
        raise PermissionDenied("Вы не можете редактировать чужую вакансию")
    
    if request.method == 'POST':
        serializer = JobSerializer(job, data=request.POST)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, 'Вакансия успешно обновлена')
            return redirect('job_detail', job_id=job.id)
        else:
            messages.error(request, 'Ошибка при обновлении вакансии')
    else:
        serializer = JobSerializer(job)
    
    departments = Department.objects.all()
    skills = Skill.objects.all()
    job_types = Job.JOB_TYPE_CHOICES
    
    return render(request, 'jobs/job_form.html', {
        'job': job,
        'serializer': serializer,
        'departments': departments,
        'skills': skills,
        'job_types': job_types
    })

@login_required
def job_delete(request, job_id):
    """Удаление вакансии"""
    job = get_object_or_404(Job, id=job_id)
    if request.user != job.employer:
        raise PermissionDenied("Вы не можете удалить чужую вакансию")
    
    if request.method == 'POST':
        job.delete()
        messages.success(request, 'Вакансия успешно удалена')
        return redirect('job_list')
    
    return render(request, 'jobs/job_confirm_delete.html', {'job': job})

@login_required
def toggle_favorite(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, job=job)
    
    if not created:
        favorite.delete()
        messages.success(request, 'Вакансия удалена из избранного')
    else:
        messages.success(request, 'Вакансия добавлена в избранное')
    
    return redirect('job_detail', job_id=job_id)

@requires_csrf_token
def favorites(request):
    if not request.user.is_authenticated:
        return redirect('login')
        
    favorites = Favorite.objects.filter(user=request.user).select_related('job')
    jobs = [favorite.job for favorite in favorites]
    return render(request, 'jobs/favorites.html', {'jobs': jobs})

@login_required
def applications(request):
    if request.user.role == 'employer':
        applications = Application.objects.filter(job__employer=request.user)
    else:
        applications = Application.objects.filter(applicant=request.user)
    return render(request, 'applications/list.html', {'applications': applications})

@login_required
def job_apply(request, job_id):
    """Подача заявки на вакансию"""
    job = get_object_or_404(Job, id=job_id)
    
    if request.user.role != 'student':
        messages.error(request, 'Только студенты могут подавать заявки на вакансии')
        return redirect('job_detail', job_id=job_id)
    
    if job.employer == request.user:
        messages.error(request, 'Вы не можете подать заявку на свою вакансию')
        return redirect('job_detail', job_id=job_id)
    
    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.error(request, 'Вы уже подали заявку на эту вакансию')
        return redirect('job_detail', job_id=job_id)
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()
            messages.success(request, 'Заявка успешно отправлена')
            return redirect('applications')
        else:
            messages.error(request, 'Ошибка при отправке заявки')
    else:
        form = ApplicationForm()
    
    return render(request, 'applications/application_form.html', {
        'form': form,
        'job': job
    })

@login_required
def cancel_application(request, application_id):
    application = get_object_or_404(Application, id=application_id, applicant=request.user)
    
    if application.status == 'pending':
        application.delete()
        messages.success(request, 'Заявка успешно отменена.')
    else:
        messages.error(request, 'Невозможно отменить заявку в текущем статусе.')
    
    return redirect('applications')

def login_view(request):
    if request.method == 'GET':
        form = AuthenticationForm()
        return render(request, 'registration/login.html', {'form': form})
    
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        login(request, user)
        messages.success(request, 'Вы успешно вошли в систему')
        return redirect('home')
    else:
        form = AuthenticationForm()
        messages.error(request, 'Неверные учетные данные')
        return render(request, 'registration/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('home')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация успешно завершена')
            return redirect('home')
        return render(request, 'registration/register.html', {'form': form})
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
        return User.objects.all()

    def get_permissions(self):
        if self.action in ['create']:
            return [AllowAny()]
        return super().get_permissions()

    def get_object(self):
        try:
            return super().get_object()
        except Http404:
            raise UserNotFoundError()

    def create(self, request, *args, **kwargs):
        validate_user_parameters(request.data)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        validate_user_parameters(request.data)
        return super().update(request, *args, **kwargs)

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Department.objects.none()
        return Department.objects.all()

    def get_object(self):
        try:
            return super().get_object()
        except Http404:
            raise DepartmentNotFoundError()

    def create(self, request, *args, **kwargs):
        validate_department_parameters(request.data)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        validate_department_parameters(request.data)
        return super().update(request, *args, **kwargs)

class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Application.objects.none()
        if self.request.user.role == 'employer':
            return Application.objects.filter(job__employer=self.request.user)
        return Application.objects.filter(applicant=self.request.user)

    def get_object(self):
        try:
            return super().get_object()
        except Http404:
            raise ApplicationNotFoundError()

    def create(self, request, *args, **kwargs):
        validate_application_parameters(request.data, request.user)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        try:
            serializer.save(applicant=self.request.user)
        except IntegrityError as e:
            raise ConflictError(detail=str(e))
        except Exception as e:
            raise ServerError(detail=str(e))

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        application = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Application.STATUS_CHOICES):
            raise InvalidApplicationStatusError()
        
        if request.user.role != 'employer' or application.job.employer != request.user:
            raise PermissionError(detail='У вас нет прав для изменения статуса этой заявки')
        
        application.status = new_status
        application.save()
        
        return Response({'status': 'success'})

class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Skill.objects.none()
        return Skill.objects.all()

class UserSkillViewSet(viewsets.ModelViewSet):
    queryset = UserSkill.objects.all()
    serializer_class = UserSkillSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return UserSkill.objects.none()
        return UserSkill.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Message.objects.none()
        return Message.objects.filter(
            models.Q(sender=self.request.user) | 
            models.Q(receiver=self.request.user)
        )

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Review.objects.none()
        return Review.objects.filter(
            models.Q(employer=self.request.user) |
            models.Q(employee=self.request.user)
        )

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'notification marked as read'})

def handler404(request, exception):
    """Обработчик 404 ошибки"""
    return render(request, 'errors/404.html', status=404)

def handler500(request):
    """Глобальный обработчик 500 ошибки"""
    print("Handler500 called!")
    try:
        return render(request, 'errors/500.html', status=500)
    except Exception as e:
        print(f"Error in handler500: {str(e)}")
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

def handler403(request, exception):
    """Обработчик 403 ошибки"""
    return render(request, 'errors/403.html', status=403)

def handler400(request, exception):
    """Обработчик 400 ошибки"""
    return render(request, 'errors/400.html', status=400)

def test_401_error(request):
    """Тестовое представление для проверки 401 ошибки"""
    raise NotAuthenticated("Требуется аутентификация")

def test_403_error(request):
    """Тестовое представление для проверки 403 ошибки"""
    raise PermissionDenied("У вас нет прав для доступа к этой странице")

def test_500_error(request):
    """Тестовое представление для проверки 500 ошибки"""
    # Намеренно создаем ошибку
    nonexistent_variable = undefined_variable
    return render(request, 'jobs/test_500.html')

@login_required
def add_review(request, job_id):
    """Добавление отзыва о вакансии"""
    job = get_object_or_404(Job, id=job_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        is_anonymous = request.POST.get('is_anonymous') == 'on'
        
        if not rating or not comment:
            messages.error(request, 'Пожалуйста, заполните все поля')
            return redirect('add_review', job_id=job_id)
        
        # Проверяем, не оставлял ли пользователь уже отзыв
        if Review.objects.filter(job=job, reviewer=request.user).exists():
            messages.error(request, 'Вы уже оставили отзыв о этой вакансии')
            return redirect('job_detail', job_id=job_id)
        
        Review.objects.create(
            job=job,
            reviewer=request.user,
            rating=rating,
            comment=comment,
            is_anonymous=is_anonymous
        )
        
        messages.success(request, 'Отзыв успешно добавлен')
        return redirect('job_detail', job_id=job_id)
    
    return render(request, 'jobs/review_form.html', {'job': job})

@login_required
def user_skills(request):
    """Страница управления навыками пользователя"""
    user_skills = UserSkill.objects.filter(user=request.user).select_related('skill')
    available_skills = Skill.objects.exclude(
        id__in=user_skills.values_list('skill_id', flat=True)
    )
    
    return render(request, 'users/skills.html', {
        'user_skills': user_skills,
        'available_skills': available_skills
    })

@login_required
def add_skill(request):
    """Добавление навыка пользователю"""
    if request.method == 'POST':
        skill_id = request.POST.get('skill')
        level = request.POST.get('level')
        
        if not skill_id or not level:
            messages.error(request, 'Пожалуйста, заполните все поля')
            return redirect('user_skills')
        
        try:
            skill = Skill.objects.get(id=skill_id)
            UserSkill.objects.create(
                user=request.user,
                skill=skill,
                level=level
            )
            messages.success(request, 'Навык успешно добавлен')
        except Skill.DoesNotExist:
            messages.error(request, 'Выбранный навык не существует')
        except IntegrityError:
            messages.error(request, 'У вас уже есть этот навык')
    
    return redirect('user_skills')

@login_required
def edit_skill(request, user_skill_id):
    """Редактирование навыка пользователя"""
    user_skill = get_object_or_404(UserSkill, id=user_skill_id, user=request.user)
    
    if request.method == 'POST':
        level = request.POST.get('level')
        if level:
            user_skill.level = level
            user_skill.save()
            messages.success(request, 'Навык успешно обновлен')
        else:
            messages.error(request, 'Пожалуйста, выберите уровень навыка')
    
    return redirect('user_skills')

@login_required
def delete_skill(request, user_skill_id):
    """Удаление навыка пользователя"""
    user_skill = get_object_or_404(UserSkill, id=user_skill_id, user=request.user)
    user_skill.delete()
    messages.success(request, 'Навык успешно удален')
    return redirect('user_skills') 