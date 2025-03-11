from rest_framework import serializers
from .models import User, Department, Application, Skill, UserSkill, Message, Review, Notification, Job

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'created_at')
        read_only_fields = ('id', 'created_at')
        extra_kwargs = {
            'username': {'help_text': 'Имя пользователя'},
            'email': {'help_text': 'Email пользователя'},
            'role': {'help_text': 'Роль пользователя (student, employer, admin)'}
        }

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'
        extra_kwargs = {
            'name': {'help_text': 'Название отдела'},
            'description': {'help_text': 'Описание отдела'},
            'location': {'help_text': 'Местоположение отдела'},
            'contact_email': {'help_text': 'Контактный email отдела'}
        }

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'
        extra_kwargs = {
            'name': {'help_text': 'Название навыка'},
            'category': {'help_text': 'Категория навыка (technical, soft, language, other)'}
        }

class ApplicationSerializer(serializers.ModelSerializer):
    applicant = UserSerializer(read_only=True)
    
    class Meta:
        model = Application
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'applicant')
        extra_kwargs = {
            'job': {'help_text': 'ID вакансии'},
            'status': {'help_text': 'Статус заявки (pending, accepted, rejected, withdrawn)'},
            'cover_letter': {'help_text': 'Сопроводительное письмо'},
            'resume': {'help_text': 'Файл резюме'}
        }

class UserSkillSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)
    
    class Meta:
        model = UserSkill
        fields = ('skill', 'level', 'verified')
        extra_kwargs = {
            'level': {'help_text': 'Уровень владения навыком (beginner, intermediate, advanced)'},
            'verified': {'help_text': 'Подтвержден ли навык'}
        }

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ('created_at', 'sender')
        extra_kwargs = {
            'receiver': {'help_text': 'ID получателя сообщения'},
            'content': {'help_text': 'Содержание сообщения'},
            'application': {'help_text': 'ID заявки (опционально)'},
            'is_read': {'help_text': 'Прочитано ли сообщение'}
        }

class ReviewSerializer(serializers.ModelSerializer):
    reviewer = UserSerializer(read_only=True)
    
    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ('created_at', 'reviewer')
        extra_kwargs = {
            'job': {'help_text': 'ID вакансии'},
            'rating': {'help_text': 'Оценка от 1 до 5'},
            'comment': {'help_text': 'Комментарий к отзыву'},
            'is_anonymous': {'help_text': 'Анонимный ли отзыв'}
        }

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('created_at',)
        extra_kwargs = {
            'user': {'help_text': 'Пользователь, которому адресовано уведомление'},
            'title': {'help_text': 'Заголовок уведомления'},
            'content': {'help_text': 'Содержание уведомления'},
            'type': {'help_text': 'Тип уведомления (application_update, new_message, deadline, system)'},
            'is_read': {'help_text': 'Прочитано ли уведомление'}
        }

class JobSerializer(serializers.ModelSerializer):
    employer = UserSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source='department',
        write_only=True,
        required=True,
        error_messages={
            'required': 'Необходимо выбрать отдел',
            'does_not_exist': 'Выбранный отдел не существует'
        },
        help_text='ID отдела (обязательное поле)'
    )
    department = DepartmentSerializer(read_only=True)
    deadline = serializers.DateField(
        required=True,
        error_messages={
            'required': 'Необходимо указать срок подачи заявок',
            'invalid': 'Неверный формат даты'
        },
        help_text='Дедлайн подачи заявок в формате ГГГГ-ММ-ДД (обязательное поле)'
    )
    
    class Meta:
        model = Job
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'employer')
        extra_kwargs = {
            'title': {
                'error_messages': {'required': 'Необходимо указать название вакансии'},
                'help_text': 'Название вакансии (обязательное поле)'
            },
            'description': {
                'error_messages': {'required': 'Необходимо указать описание вакансии'},
                'help_text': 'Описание вакансии (обязательное поле)'
            },
            'job_type': {
                'error_messages': {'required': 'Необходимо выбрать тип вакансии'},
                'help_text': 'Тип вакансии: internship, part_time, research, teaching (обязательное поле)'
            },
            'salary': {'help_text': 'Зарплата (опционально)'},
            'is_active': {'help_text': 'Активна ли вакансия'}
        }
    
    def validate_deadline(self, value):
        """
        Преобразует дату в datetime для сохранения в модели
        """
        from datetime import datetime, time
        if isinstance(value, datetime):
            return value
        # Если приходит только дата, добавляем время 23:59:59
        return datetime.combine(value, time(23, 59, 59))
    
    def validate(self, data):
        """
        Дополнительная валидация всех полей формы
        """
        # Выводим данные для отладки
        print(f"Данные в validate: {data}")
        return data 