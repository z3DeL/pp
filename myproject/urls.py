from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.routers import DefaultRouter
from . import views
from .api.viewsets import (
    UserViewSet, DepartmentViewSet, ApplicationViewSet,
    SkillViewSet, UserSkillViewSet, MessageViewSet, ReviewViewSet,
    NotificationViewSet, JobViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'applications', ApplicationViewSet, basename='application')
router.register(r'skills', SkillViewSet)
router.register(r'user-skills', UserSkillViewSet, basename='user-skill')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'jobs', JobViewSet)

schema_view = get_schema_view(
    openapi.Info(
        title="Job Portal API",
        default_version='v1',
        description="API для портала вакансий",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

handler500 = 'myproject.views.handler500'
handler404 = 'myproject.views.handler404'
handler403 = 'myproject.views.handler403'
handler400 = 'myproject.views.handler400'

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API URLs
    path('api/', include(router.urls)),
    path('api/favorites/', views.api_favorites, name='api_favorites'),
    path('api/applications/', views.api_applications, name='api_applications'),
    
    # Swagger URLs
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Web URLs
    path('', views.home, name='home'),
    path('jobs/', views.job_list_view, name='job_list'),
    path('jobs/create/', views.job_create, name='job_create'),
    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),
    path('jobs/<int:job_id>/edit/', views.job_edit, name='job_edit'),
    path('jobs/<int:job_id>/delete/', views.job_delete, name='job_delete'),
    path('jobs/<int:job_id>/apply/', views.job_apply, name='job_apply'),
    path('jobs/<int:job_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('jobs/<int:job_id>/review/', views.add_review, name='add_review'),
    path('favorites/', views.favorites, name='favorites'),
    path('applications/', views.applications, name='applications'),
    path('applications/<int:application_id>/', views.application_detail, name='application_detail'),
    path('applications/<int:application_id>/update-status/', views.update_application_status, name='update_application_status'),
    path('applications/<int:application_id>/cancel/', views.cancel_application, name='cancel_application'),
    path('applications/<int:application_id>/resume/download/', views.download_resume, name='download_application_resume'),
    path('send-message/', views.send_message, name='send_message'),
    path('messages/', views.messages_list, name='messages_list'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    
    # Профиль пользователя
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/skills/', views.profile_skills, name='profile_skills'),
    path('profile/skills/<int:skill_id>/delete/', views.delete_profile_skill, name='delete_profile_skill'),
    path('profile/<str:username>/', views.profile_view, name='user_profile'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 