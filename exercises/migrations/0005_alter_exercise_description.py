# Generated by Django 5.1.1 on 2024-10-18 07:23

import ckeditor_uploader.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('exercises', '0004_alter_exercise_language'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exercise',
            name='description',
            field=ckeditor_uploader.fields.RichTextUploadingField(null=True),
        ),
    ]
