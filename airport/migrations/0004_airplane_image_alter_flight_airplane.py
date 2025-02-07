# Generated by Django 5.1.5 on 2025-02-02 22:24

import airport.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("airport", "0003_flight_crew"),
    ]

    operations = [
        migrations.AddField(
            model_name="airplane",
            name="image",
            field=models.ImageField(
                null=True, upload_to=airport.models.airplane_image_file_path
            ),
        ),
        migrations.AlterField(
            model_name="flight",
            name="airplane",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="airport.airplane"
            ),
        ),
    ]
