from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.job_list, name='home'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),
    path('jobs/<int:job_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('jobs/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    path('favorites/', views.favorites, name='favorites'),
    path('applications/', views.applications, name='applications'),
    # Маршруты для авторизации
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
] 