# Generated by Django 5.1.1 on 2024-09-23 17:39

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_order_time_completed_order_time_created_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='user',
        ),
        migrations.AddField(
            model_name='product',
            name='count_type',
            field=models.CharField(choices=[('inf', 'Нужно считать количество'), ('non-inf', 'Не нужно считать количество')], default='non-inf', max_length=7),
        ),
        migrations.AddField(
            model_name='product',
            name='stock',
            field=models.IntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='product',
            name='is_available',
            field=models.BooleanField(default=True),
        ),
        migrations.CreateModel(
            name='Shift',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('is_active', models.BooleanField(default=True)),
                ('orders', models.ManyToManyField(related_name='shifts', to='main.order')),
            ],
        ),
    ]
