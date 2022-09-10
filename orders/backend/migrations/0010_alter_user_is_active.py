# Generated by Django 4.0.4 on 2022-09-09 10:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0009_confirmemailtoken'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='is_active',
            field=models.BooleanField(default=False, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active'),
        ),
    ]
