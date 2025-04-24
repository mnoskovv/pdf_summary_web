from django.db import migrations
from django.contrib.auth.hashers import make_password

def create_superuser_and_settings(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    OpenaiSettings = apps.get_model('app', 'OpenaiSettings')

    if not User.objects.filter(username='admin').exists():
        User.objects.create(
            username='admin',
            is_superuser=True,
            is_staff=True,
            password=make_password('admin')
        )

    OpenaiSettings.objects.create(
        model="gpt-3.5-turbo",
        temperature=0.5,
        max_retries=3,
        summary_prompt="prompt:"
    )

class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_superuser_and_settings),
    ]
