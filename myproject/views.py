from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Job, Department, Skill, Application, UserSkill, JobSkill
from django.http import JsonResponse
from django.contrib import messages

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

@login_required
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