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
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .forms import ApplicationForm, UserRegistrationForm
from rest_framework.response import Response
from .serializers import (
    ApplicationSerializer, UserSerializer,
    SkillSerializer, UserSkillSerializer,
    MessageSerializer, ReviewSerializer, NotificationSerializer
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_applications(request):
    if request.user.role == 'employer':
        applications = Application.objects.filter(job__employer=request.user)
    else:
        applications = Application.objects.filter(applicant=request.user)
    
    serializer = ApplicationSerializer(applications, many=True)
    return Response(serializer.data)

# Web Views
def home(request):
    jobs = Job.objects.filter(is_active=True).order_by('-created_at')[:5]
    return render(request, 'home.html', {'jobs': jobs})

def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    return render(request, 'jobs/detail.html', {'job': job})

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