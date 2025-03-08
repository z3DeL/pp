from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Job, Department, Skill, Application, UserSkill, JobSkill
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

@swagger_auto_schema(
    method='get',
    operation_description="Получить список всех вакансий",
    manual_parameters=[
        openapi.Parameter('job_type', openapi.IN_QUERY, description="Тип вакансии", type=openapi.TYPE_STRING),
        openapi.Parameter('department', openapi.IN_QUERY, description="ID отдела", type=openapi.TYPE_INTEGER),
        openapi.Parameter('skills', openapi.IN_QUERY, description="ID навыков", type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER)),
        openapi.Parameter('schedule', openapi.IN_QUERY, description="График работы", type=openapi.TYPE_STRING),
        openapi.Parameter('sort', openapi.IN_QUERY, description="Сортировка", type=openapi.TYPE_STRING),
        openapi.Parameter('page', openapi.IN_QUERY, description="Номер страницы", type=openapi.TYPE_INTEGER),
    ]
)
@api_view(['GET'])
def job_list(request):
    # Получаем параметры фильтрации
    job_type = request.GET.get('job_type')
    department_id = request.GET.get('department')
    skills = request.GET.getlist('skills')
    schedule = request.GET.get('schedule')
    sort_by = request.GET.get('sort', '-created_at')
    
    # Начинаем с базового QuerySet
    jobs = Job.objects.filter(is_active=True)
    
    # Применяем фильтры
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    
    if department_id:
        jobs = jobs.filter(department_id=department_id)
    
    if skills:
        jobs = jobs.filter(required_skills__id__in=skills).distinct()
    
    if schedule:
        jobs = jobs.filter(schedule=schedule)
    
    # Сортировка
    jobs = jobs.order_by(sort_by)
    
    # Пагинация
    paginator = Paginator(jobs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получаем все департаменты и навыки для фильтров
    departments = Department.objects.all()
    all_skills = Skill.objects.all()
    
    context = {
        'jobs': page_obj,
        'departments': departments,
        'skills': all_skills,
        'is_paginated': True,
        'page_obj': page_obj,
    }
    
    return render(request, 'job_list.html', context)

@swagger_auto_schema(
    method='get',
    operation_description="Получить детальную информацию о вакансии",
    manual_parameters=[
        openapi.Parameter('job_id', openapi.IN_PATH, description="ID вакансии", type=openapi.TYPE_INTEGER),
    ]
)
@api_view(['GET'])
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    required_skills = JobSkill.objects.filter(job=job, is_required=True)
    optional_skills = JobSkill.objects.filter(job=job, is_required=False)
    
    context = {
        'job': job,
        'required_skills': required_skills,
        'optional_skills': optional_skills,
    }
    return render(request, 'job_detail.html', context)

@swagger_auto_schema(
    method='post',
    operation_description="Добавить/удалить вакансию из избранного",
    manual_parameters=[
        openapi.Parameter('job_id', openapi.IN_PATH, description="ID вакансии", type=openapi.TYPE_INTEGER),
    ],
    responses={
        200: openapi.Response("Успешное выполнение"),
        404: openapi.Response("Вакансия не найдена"),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_POST
def toggle_favorite(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    if request.user in job.favorites.all():
        job.favorites.remove(request.user)
        is_favorite = False
    else:
        job.favorites.add(request.user)
        is_favorite = True
    return JsonResponse({'is_favorite': is_favorite})

@login_required
def favorites(request):
    favorite_jobs = Job.objects.filter(favorites=request.user)
    return render(request, 'favorites.html', {'jobs': favorite_jobs})

@login_required
def applications(request):
    user_applications = Application.objects.filter(applicant=request.user)
    return render(request, 'applications.html', {'applications': user_applications})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.POST.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('home')
            else:
                messages.error(request, 'Неверное имя пользователя или пароль.')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('home')

@swagger_auto_schema(
    method='post',
    operation_description="Подать заявку на вакансию",
    manual_parameters=[
        openapi.Parameter('job_id', openapi.IN_PATH, description="ID вакансии", type=openapi.TYPE_INTEGER),
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'cover_letter': openapi.Schema(type=openapi.TYPE_STRING),
            'resume': openapi.Schema(type=openapi.TYPE_FILE),
        }
    ),
    responses={
        200: openapi.Response("Заявка успешно создана"),
        400: openapi.Response("Ошибка валидации"),
        404: openapi.Response("Вакансия не найдена"),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    # Проверяем, не подана ли уже заявка
    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.error(request, 'Вы уже подали заявку на эту вакансию.')
        return redirect('job_detail', job_id=job_id)
    
    # Проверяем, не истек ли срок подачи
    if job.deadline < timezone.now():
        messages.error(request, 'Срок подачи заявки истек.')
        return redirect('job_detail', job_id=job_id)
    
    # Создаем новую заявку
    application = Application.objects.create(
        job=job,
        applicant=request.user,
        status='pending',
        cover_letter=request.POST.get('cover_letter', ''),
        resume=request.FILES.get('resume')
    )
    
    messages.success(request, 'Ваша заявка успешно отправлена.')
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

@swagger_auto_schema(
    method='get',
    operation_description="Страница регистрации пользователя",
    responses={
        200: openapi.Response("Страница регистрации"),
    }
)
@swagger_auto_schema(
    method='post',
    operation_description="Регистрация нового пользователя",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING),
            'email': openapi.Schema(type=openapi.TYPE_STRING),
            'password1': openapi.Schema(type=openapi.TYPE_STRING),
            'password2': openapi.Schema(type=openapi.TYPE_STRING),
            'role': openapi.Schema(type=openapi.TYPE_STRING),
        }
    ),
    responses={
        200: openapi.Response("Пользователь успешно зарегистрирован"),
        400: openapi.Response("Ошибка валидации"),
    }
)
@api_view(['GET', 'POST'])
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Регистрация успешно завершена. Теперь вы можете войти.')
            return redirect('login')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

@swagger_auto_schema(
    method='get',
    operation_description="Главная страница",
    responses={
        200: openapi.Response("Главная страница"),
    }
)
@api_view(['GET'])
def home(request):
    latest_jobs = Job.objects.filter(is_active=True).order_by('-created_at')[:5]
    return render(request, 'home.html', {'latest_jobs': latest_jobs}) 