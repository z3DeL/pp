from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Department, Job, Application, Skill, JobSkill, UserSkill, Message, Review, Notification

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {'fields': ('role',)}),
    )

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'contact_email', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'employer', 'job_type', 'salary', 'deadline', 'is_active')
    list_filter = ('job_type', 'is_active', 'department', 'created_at', 'deadline')
    search_fields = ('title', 'description', 'requirements')
    date_hierarchy = 'created_at'

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('job', 'applicant', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('job__title', 'applicant__username', 'cover_letter')
    date_hierarchy = 'created_at'

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)

@admin.register(JobSkill)
class JobSkillAdmin(admin.ModelAdmin):
    list_display = ('job', 'skill', 'is_required', 'level')
    list_filter = ('is_required', 'level')
    search_fields = ('job__title', 'skill__name')

@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill', 'level', 'verified')
    list_filter = ('level', 'verified')
    search_fields = ('user__username', 'skill__name')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__username', 'receiver__username', 'content')
    date_hierarchy = 'created_at'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('job', 'reviewer', 'rating', 'is_anonymous', 'created_at')
    list_filter = ('rating', 'is_anonymous', 'created_at')
    search_fields = ('job__title', 'reviewer__username', 'comment')
    date_hierarchy = 'created_at'

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'type', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'content')
    date_hierarchy = 'created_at' 