from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ("lms", "0003_subscription"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="updated_at",
            field=models.DateTimeField(
                auto_now=True, default=timezone.now, verbose_name="Дата обновления"
            ),
            preserve_default=False,
        ),
    ]
