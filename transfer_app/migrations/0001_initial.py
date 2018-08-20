# Generated by Django 2.0.6 on 2018-08-06 21:52

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(max_length=100)),
                ('path', models.CharField(max_length=1000)),
                ('size', models.BigIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('expiration_date', models.DateTimeField(null=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Transfer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('download', models.BooleanField()),
                ('destination', models.CharField(max_length=1000)),
                ('completed', models.BooleanField(default=False)),
                ('success', models.BooleanField(default=False)),
                ('start_time', models.DateTimeField(auto_now_add=True)),
                ('finish_time', models.DateTimeField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TransferCoordinator',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completed', models.BooleanField(default=False)),
                ('start_time', models.DateTimeField(auto_now_add=True)),
                ('finish_time', models.DateTimeField(null=True)),
            ],
        ),
        migrations.AddField(
            model_name='transfer',
            name='coordinator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='transfer_app.TransferCoordinator'),
        ),
        migrations.AddField(
            model_name='transfer',
            name='resource',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='transfer_app.Resource'),
        ),
    ]
