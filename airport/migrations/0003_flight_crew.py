# Generated by Django 5.1.5 on 2025-01-31 14:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("airport", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="flight",
            name="crew",
            field=models.ManyToManyField(to="airport.crew"),
        ),
    ]
