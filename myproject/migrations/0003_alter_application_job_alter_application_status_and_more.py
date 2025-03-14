# Generated by Django 5.0.2 on 2025-03-08 12:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myproject', '0002_alter_user_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='myproject.job'),
        ),
        migrations.AlterField(
            model_name='application',
            name='status',
            field=models.CharField(choices=[('pending', 'На рассмотрении'), ('accepted', 'Принята'), ('rejected', 'Отклонена'), ('withdrawn', 'Отозвана')], default='pending', max_length=20),
        ),
        migrations.AlterUniqueTogether(
            name='application',
            unique_together={('job', 'applicant')},
        ),
    ]
