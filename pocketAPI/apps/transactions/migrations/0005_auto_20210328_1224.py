# Generated by Django 3.1.7 on 2021-03-28 12:24

from django.db import migrations, models
import transactions.helpers


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0004_auto_20210327_1251'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pockettransaction',
            name='status',
            field=models.PositiveIntegerField(choices=[(1, 'CREATED'), (2, 'IN_PROCESS'), (3, 'CONFIRMED'), (4, 'FINISHED'), (5, 'CANCELLED')], default=transactions.helpers.TransactionStatus['CREATED'], verbose_name='status'),
        ),
    ]