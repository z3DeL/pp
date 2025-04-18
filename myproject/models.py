from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Студент'),
        ('employer', 'Работодатель'),
        ('admin', 'Администратор'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=250, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    birth_date = models.DateField(null=True, blank=True)
    experience = models.TextField(blank=True, null=True)
    education = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Профиль {self.user.username}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Department(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    contact_email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Job(models.Model):
    JOB_TYPE_CHOICES = [
        ('internship', 'Стажировка'),
        ('part_time', 'Частичная занятость'),
        ('research', 'Исследовательская работа'),
        ('teaching', 'Преподавательская работа')
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    employer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_jobs')
    job_type = models.CharField(max_length=50, choices=JOB_TYPE_CHOICES)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='favorites')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'job']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.job.title}"

class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('accepted', 'Принята'),
        ('rejected', 'Отклонена'),
        ('withdrawn', 'Отозвана'),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    cover_letter = models.TextField()
    resume = models.FileField(upload_to='resumes/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['job', 'applicant']
    
    def __str__(self):
        return f"{self.applicant.username} - {self.job.title}"
    
    @property
    def status_color(self):
        colors = {
            'pending': 'warning',
            'accepted': 'success',
            'rejected': 'danger',
            'withdrawn': 'secondary',
        }
        return colors.get(self.status, 'primary')

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, choices=[
        ('technical', 'Технические'),
        ('soft', 'Soft skills'),
        ('language', 'Языки'),
        ('other', 'Другие')
    ])

    def __str__(self):
        return self.name

class JobSkill(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='required_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    is_required = models.BooleanField(default=True)
    level = models.CharField(max_length=20, choices=[
        ('beginner', 'Начальный'),
        ('intermediate', 'Средний'),
        ('advanced', 'Продвинутый')
    ])

    def __str__(self):
        return f"{self.job.title} - {self.skill.name}"

class UserSkill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    level = models.CharField(max_length=20, choices=[
        ('beginner', 'Начальный'),
        ('intermediate', 'Средний'),
        ('advanced', 'Продвинутый')
    ])
    verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.skill.name}"

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    application = models.ForeignKey(Application, on_delete=models.CASCADE, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"От {self.sender.username} к {self.receiver.username}"

class Review(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_anonymous = models.BooleanField(default=False)

    def __str__(self):
        return f"Отзыв о {self.job.title} от {self.reviewer.username}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    type = models.CharField(max_length=50, choices=[
        ('application_update', 'Обновление заявки'),
        ('new_message', 'Новое сообщение'),
        ('deadline', 'Дедлайн'),
        ('system', 'Системное')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.title 