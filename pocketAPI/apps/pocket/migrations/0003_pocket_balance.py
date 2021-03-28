# Generated by Django 3.1.7 on 2021-03-26 11:06

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pocket', '0002_auto_20210324_2120'),
    ]

    operations = [
        migrations.AddField(
            model_name='pocket',
            name='balance',
            field=models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]