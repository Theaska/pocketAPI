# Generated by Django 3.1.7 on 2021-03-24 21:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Pocket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(db_index=True, default=uuid.UUID('a3322f0a-7500-4fb5-a296-bcad2b827141'), editable=False, unique=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=128, verbose_name='name of pocket')),
                ('description', models.TextField(blank=True, max_length=512, null=True, verbose_name='description of pocket')),
                ('is_archived', models.BooleanField(default=False, verbose_name='in archive')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pockets', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Pocket',
                'verbose_name_plural': 'Pockets',
            },
        ),
    ]
