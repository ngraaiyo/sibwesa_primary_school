# Fixed version of migration 0008 to prevent model deletion errors
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_examination_subject_class_student_mark'),
    ]

    operations = [
        # 🚫 We intentionally leave this empty to skip deleting models or fields
        # because removing them caused FieldDoesNotExist errors in later migrations.
    ]
