from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from myproject.models import Department, Job, Skill, JobSkill, UserSkill, Review, Notification
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Загружает тестовые данные в базу данных'

    def handle(self, *args, **kwargs):
        # Создаем суперпользователя
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('Создан суперпользователь admin'))

        # Создаем тестового работодателя
        employer, created = User.objects.get_or_create(
            username='employer',
            defaults={
                'email': 'employer@example.com',
                'role': 'employer',
                'is_staff': True
            }
        )
        if created:
            employer.set_password('employer123')
            employer.save()
            self.stdout.write(self.style.SUCCESS('Создан работодатель employer'))

        # Создаем тестового студента
        student, created = User.objects.get_or_create(
            username='student',
            defaults={
                'email': 'student@example.com',
                'role': 'student'
            }
        )
        if created:
            student.set_password('student123')
            student.save()
            self.stdout.write(self.style.SUCCESS('Создан студент student'))

        # Создаем отделы
        departments = [
            {
                'name': 'Кафедра информатики',
                'description': 'Кафедра, занимающаяся обучением в области информационных технологий',
                'location': 'Корпус 1, этаж 3',
                'contact_email': 'cs@university.edu'
            },
            {
                'name': 'Кафедра математики',
                'description': 'Кафедра, специализирующаяся на математических науках',
                'location': 'Корпус 2, этаж 4',
                'contact_email': 'math@university.edu'
            }
        ]

        for dept_data in departments:
            department, created = Department.objects.get_or_create(
                name=dept_data['name'],
                defaults=dept_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Создан отдел {department.name}'))

        # Создаем навыки
        skills = [
            {'name': 'Python', 'category': 'technical'},
            {'name': 'JavaScript', 'category': 'technical'},
            {'name': 'SQL', 'category': 'technical'},
            {'name': 'Коммуникабельность', 'category': 'soft'},
            {'name': 'Английский язык', 'category': 'language'},
            {'name': 'Управление проектами', 'category': 'soft'}
        ]

        for skill_data in skills:
            skill, created = Skill.objects.get_or_create(
                name=skill_data['name'],
                defaults=skill_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Создан навык {skill.name}'))

        # Создаем вакансии
        jobs = [
            {
                'title': 'Стажер-программист Python',
                'description': 'Разработка веб-приложений на Python/Django',
                'department': Department.objects.get(name='Кафедра информатики'),
                'employer': employer,
                'job_type': 'internship',
                'requirements': 'Базовые знания Python, SQL, HTML/CSS',
                'salary': 30000,
                'deadline': timezone.now() + timedelta(days=30)
            },
            {
                'title': 'Преподаватель математики',
                'description': 'Проведение практических занятий по математике',
                'department': Department.objects.get(name='Кафедра математики'),
                'employer': employer,
                'job_type': 'teaching',
                'requirements': 'Высшее математическое образование, опыт преподавания',
                'salary': 45000,
                'deadline': timezone.now() + timedelta(days=45)
            }
        ]

        for job_data in jobs:
            job, created = Job.objects.get_or_create(
                title=job_data['title'],
                defaults=job_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Создана вакансия {job.title}'))

                # Добавляем навыки для вакансий
                if job.title == 'Стажер-программист Python':
                    required_skills = [
                        ('Python', 'advanced'),
                        ('SQL', 'intermediate'),
                        ('Английский язык', 'intermediate')
                    ]
                else:
                    required_skills = [
                        ('Управление проектами', 'intermediate'),
                        ('Коммуникабельность', 'advanced'),
                        ('Английский язык', 'intermediate')
                    ]

                for skill_name, level in required_skills:
                    skill = Skill.objects.get(name=skill_name)
                    JobSkill.objects.create(
                        job=job,
                        skill=skill,
                        is_required=True,
                        level=level
                    )

        # Добавляем навыки студенту
        student_skills = [
            ('Python', 'intermediate'),
            ('JavaScript', 'beginner'),
            ('SQL', 'intermediate'),
            ('Коммуникабельность', 'advanced'),
            ('Английский язык', 'intermediate')
        ]

        for skill_name, level in student_skills:
            skill = Skill.objects.get(name=skill_name)
            UserSkill.objects.get_or_create(
                user=student,
                skill=skill,
                defaults={'level': level}
            )

        # Создаем отзывы
        reviews = [
            {
                'job': Job.objects.get(title='Стажер-программист Python'),
                'reviewer': student,
                'rating': 5,
                'comment': 'Отличная возможность для начинающих разработчиков!',
                'is_anonymous': False
            }
        ]

        for review_data in reviews:
            review, created = Review.objects.get_or_create(
                job=review_data['job'],
                reviewer=review_data['reviewer'],
                defaults=review_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Создан отзыв для вакансии {review.job.title}'))

        # Создаем уведомления
        notifications = [
            {
                'user': student,
                'title': 'Добро пожаловать!',
                'content': 'Спасибо за регистрацию в системе. Теперь вы можете искать вакансии и подавать заявки.',
                'type': 'system'
            }
        ]

        for notification_data in notifications:
            notification, created = Notification.objects.get_or_create(
                user=notification_data['user'],
                title=notification_data['title'],
                defaults=notification_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Создано уведомление для пользователя {notification.user.username}'))

        self.stdout.write(self.style.SUCCESS('Тестовые данные успешно загружены!')) 