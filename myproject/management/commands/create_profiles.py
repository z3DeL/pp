from django.core.management.base import BaseCommand
from myproject.models import User, Profile

class Command(BaseCommand):
    help = 'Создание профилей для существующих пользователей, у которых их нет'

    def handle(self, *args, **options):
        users_without_profile = []
        for user in User.objects.all():
            try:
                # Пробуем получить профиль пользователя
                profile = user.profile
            except Profile.DoesNotExist:
                # Если профиля нет, создаем его
                Profile.objects.create(user=user)
                users_without_profile.append(user.username)
        
        if users_without_profile:
            self.stdout.write(self.style.SUCCESS(
                f'Успешно созданы профили для {len(users_without_profile)} пользователей: {", ".join(users_without_profile)}'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('Все пользователи уже имеют профили.')) 