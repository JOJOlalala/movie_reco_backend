# Generated by Django 3.1.7 on 2021-03-22 04:09

import api_basic.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_basic', '0012_usertask_createtime'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usertask',
            name='originalVideo',
            field=models.FileField(upload_to=api_basic.models.video_upload_path, validators=[api_basic.models.userTask_validation]),
        ),
    ]