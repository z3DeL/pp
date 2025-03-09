from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Job, Department, Skill, Application, UserSkill, JobSkill, User, Message, Review, Notification
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
    DepartmentSerializer
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
    return render(request, 'jobs/list.html', {
        'jobs': queryset,
        'departments': departments
    })

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

@api_view(['GET'])
@permission_classes([AllowAny])
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
        return render(request, 'jobs/detail.html', {'job': job})
    except Job.DoesNotExist:
        if request.accepted_renderer.format == 'json':
            raise NotFoundError(detail='Вакансия не найдена')
        raise Http404('Вакансия не найдена')

@login_required
def toggle_favorite(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    if request.user in job.favorites.all():
        job.favorites.remove(request.user)
        messages.success(request, 'Вакансия удалена из избранного')
    else:
        job.favorites.add(request.user)
        messages.success(request, 'Вакансия добавлена в избранное')
    return redirect('job_detail', job_id=job_id)

@login_required
def favorites(request):
    jobs = Job.objects.filter(favorites=request.user)
    return render(request, 'jobs/favorites.html', {'jobs': jobs})

@login_required
def applications(request):
    if request.user.role == 'employer':
        applications = Application.objects.filter(job__employer=request.user)
    else:
        applications = Application.objects.filter(applicant=request.user)
    return render(request, 'applications/list.html', {'applications': applications})

@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    if job.deadline < timezone.now():
        messages.error(request, 'Срок подачи заявки истек')
        return redirect('job_detail', job_id=job_id)
    
    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.error(request, 'Вы уже подали заявку на эту вакансию')
        return redirect('job_detail', job_id=job_id)
    
    Application.objects.create(
        job=job,
        applicant=request.user,
        status='pending'
    )
    
    messages.success(request, 'Заявка успешно отправлена')
    return redirect('applications')

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
    """Обработчик ошибки 404 - страница не найдена"""
    error = {
        'code': '404',
        'message': 'Страница не найдена',
        'details': 'Запрашиваемая страница не существует или была перемещена.',
        'suggestions': [
            'Проверьте правильность введенного адреса',
            'Убедитесь, что в адресе нет опечаток',
            'Воспользуйтесь поиском или меню сайта',
            'Вернитесь на главную страницу'
        ]
    }
    return render(request, 'errors/error.html', {'error': error}, status=404)

def handler500(request):
    """Обработчик ошибки 500 - внутренняя ошибка сервера"""
    error = {
        'code': '500',
        'message': 'Внутренняя ошибка сервера',
        'details': 'На сервере произошла непредвиденная ошибка.',
        'suggestions': [
            'Попробуйте обновить страницу',
            'Попробуйте повторить действие позже',
            'Если проблема повторяется, обратитесь в службу поддержки'
        ]
    }
    return render(request, 'errors/error.html', {'error': error}, status=500)

def handler403(request, exception):
    """Обработчик ошибки 403 - доступ запрещен"""
    error = {
        'code': '403',
        'message': 'Доступ запрещен',
        'details': 'У вас нет прав для доступа к этой странице.',
        'suggestions': [
            'Убедитесь, что вы вошли в систему',
            'Проверьте, есть ли у вас необходимые права',
            'Обратитесь к администратору для получения доступа'
        ]
    }
    return render(request, 'errors/error.html', {'error': error}, status=403)

def handler400(request, exception):
    """Обработчик ошибки 400 - некорректный запрос"""
    error = {
        'code': '400',
        'message': 'Некорректный запрос',
        'details': 'Сервер не может обработать ваш запрос из-за некорректных данных.',
        'suggestions': [
            'Проверьте правильность введенных данных',
            'Убедитесь, что все обязательные поля заполнены',
            'Проверьте формат данных'
        ]
    }
    return render(request, 'errors/error.html', {'error': error}, status=400) 