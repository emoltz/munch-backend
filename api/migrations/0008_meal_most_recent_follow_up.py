# Generated by Django 5.0.3 on 2024-05-29 18:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_meal_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='meal',
            name='most_recent_follow_up',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]