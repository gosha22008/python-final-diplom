# Generated by Django 4.0.4 on 2022-08-15 15:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0002_parameter_productinfo_external_id_and_more'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='orderitem',
            constraint=models.UniqueConstraint(fields=('order_id', 'product_info'), name='unique_order_item'),
        ),
        migrations.AddConstraint(
            model_name='productinfo',
            constraint=models.UniqueConstraint(fields=('product', 'shop', 'external_id'), name='unique_product_info'),
        ),
    ]
