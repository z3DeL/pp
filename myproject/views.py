from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Job, Department, Skill
from django.http import JsonResponse

def job_list(request):
    # Получаем параметры фильтрации
    job_type = request.GET.get('job_type')
    department_id = request.GET.get('department')
    skills = request.GET.getlist('skills')
    schedule = request.GET.get('schedule')
    sort_by = request.GET.get('sort', '-created_at')
    
    # Начинаем с базового QuerySet
    jobs = Job.objects.all()
    
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

@login_required
def toggle_favorite(request, job_id):
    job = Job.objects.get(id=job_id)
    if job in request.user.favorites.all():
        request.user.favorites.remove(job)
    else:
        request.user.favorites.add(job)
    return JsonResponse({'status': 'success'})

@login_required
def favorites(request):
    jobs = request.user.favorites.all()
    context = {
        'jobs': jobs,
    }
    return render(request, 'favorites.html', context)

@login_required
def applications(request):
    applications = request.user.applications.all()
    context = {
        'applications': applications,
    }
    return render(request, 'applications.html', context) 