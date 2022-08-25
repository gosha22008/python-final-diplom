# Generated by Django 4.0.4 on 2022-08-24 13:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0006_alter_order_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('basket', 'Статус корзины'), ('new', 'Новый'), ('confirmed', 'Подтвержден'), ('assembled', 'Собран'), ('sent', 'Отправлен'), ('delivered', 'Доставлен'), ('canceled', 'Отменен')], max_length=20, verbose_name='статус заказа'),
        ),
    ]
