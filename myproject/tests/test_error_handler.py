from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import User, Job, Department, Application
from django.utils import timezone

class ErrorHandlerTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.department = Department.objects.create(name='Test Department')
        self.job = Job.objects.create(
            title='Test Job',
            description='Test Description',
            department=self.department,
            employer=self.user,
            deadline=timezone.now() + timezone.timedelta(days=7)
        )
        # Создаем тестовый файл резюме
        self.test_resume = SimpleUploadedFile(
            "resume.pdf",
            b"file_content",
            content_type="application/pdf"
        )

    def test_not_found_error(self):
        """Тест ошибки 404 - ресурс не найден"""
        response = self.client.get(
            reverse('job_detail', kwargs={'job_id': 99999}),
            HTTP_ACCEPT='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error']['code'], 'not_found')
        # Проверяем рекомендации
        self.assertIn('suggestions', response.json()['error'])
        suggestions = response.json()['error']['suggestions']
        self.assertIn('Проверьте правильность URL', suggestions)
        self.assertIn('Убедитесь, что запрашиваемый ресурс существует', suggestions)
        self.assertIn('Попробуйте обновить страницу', suggestions)

    def test_authentication_error(self):
        """Тест ошибки 401 - не авторизован"""
        response = self.client.get(
            reverse('api_applications'),
            HTTP_ACCEPT='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error']['code'], 'authentication_error')
        # Проверяем рекомендации
        self.assertIn('suggestions', response.json()['error'])
        suggestions = response.json()['error']['suggestions']
        self.assertIn('Проверьте правильность логина и пароля', suggestions)
        self.assertIn('Убедитесь, что вы авторизованы в системе', suggestions)
        self.assertIn('Попробуйте перезайти в систему', suggestions)

    def test_permission_error(self):
        """Тест ошибки 403 - нет прав"""
        self.client.login(username='testuser', password='testpass123')
        # Создаем вакансию от текущего пользователя
        job = Job.objects.create(
            title='Test Job',
            description='Test Description',
            department=self.department,
            employer=self.user,  # Важно: вакансия создается текущим пользователем
            deadline=timezone.now() + timezone.timedelta(days=7)
        )
        # Пытаемся создать заявку на свою же вакансию
        response = self.client.post(
            reverse('api_applications'),
            {
                'job': job.id,
                'cover_letter': 'Test cover letter',
                'resume': self.test_resume
            },
            HTTP_ACCEPT='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error']['code'], 'permission_error')
        # Проверяем рекомендации
        self.assertIn('suggestions', response.json()['error'])
        suggestions = response.json()['error']['suggestions']
        self.assertIn('Убедитесь, что у вас есть необходимые права', suggestions)
        self.assertIn('Обратитесь к администратору для получения доступа', suggestions)
        self.assertIn('Проверьте роль пользователя в системе', suggestions)

    def test_validation_error(self):
        """Тест ошибки 400 - неверные данные"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('api_applications'),
            {'job': 'invalid_id'},
            content_type='application/json',
            HTTP_ACCEPT='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error']['code'], 'validation_error')
        # Проверяем рекомендации
        self.assertIn('suggestions', response.json()['error'])
        suggestions = response.json()['error']['suggestions']
        self.assertIn('Проверьте правильность введенных данных', suggestions)
        self.assertIn('Убедитесь, что все обязательные поля заполнены', suggestions)
        self.assertIn('Проверьте формат данных', suggestions)

    def test_conflict_error(self):
        """Тест ошибки 409 - конфликт"""
        self.client.login(username='testuser', password='testpass123')
        # Создаем работодателя
        employer = User.objects.create_user(
            username='employer',
            password='testpass123'
        )
        # Создаем вакансию от работодателя
        job = Job.objects.create(
            title='Test Job',
            description='Test Description',
            department=self.department,
            employer=employer,  # Важно: вакансия от другого пользователя
            deadline=timezone.now() + timezone.timedelta(days=7)
        )
        # Создаем первую заявку
        Application.objects.create(
            job=job,
            applicant=self.user,
            status='pending'
        )
        # Пытаемся создать вторую заявку
        response = self.client.post(
            reverse('api_applications'),
            {
                'job': job.id,
                'cover_letter': 'Test cover letter',
                'resume': self.test_resume
            },
            HTTP_ACCEPT='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error']['code'], 'application_already_exists')
        # Проверяем рекомендации
        self.assertIn('suggestions', response.json()['error'])
        suggestions = response.json()['error']['suggestions']
        self.assertIn('Проверьте уникальность данных', suggestions)
        self.assertIn('Убедитесь, что ресурс не существует', suggestions)
        self.assertIn('Попробуйте использовать другой идентификатор', suggestions) 