# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import RegexValidator
from django.utils import timezone
from django.conf import settings

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('headteacher', 'Head Teacher'), 
        ('class_teacher', 'Class Teacher'),
        ('academic_teacher', 'Academic Teacher'),
        ('statistic_teacher', 'Statistic Teacher'),
        ('subject_teacher', 'Subject Teacher'),
    )
    
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'), # Optional: for inclusivity
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='academic_teacher')
    is_approved = models.BooleanField(default=False)

    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$',
                                 message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex], 
                                    max_length=17, 
                                    blank=True, 
                                    null=True, 
                                    unique=True
                                    )

    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True) # <-- ADD THIS FIELD if it's not there

    # New fields for security questions
    security_question_1 = models.CharField(max_length=255, blank=True, null=True)
    security_answer_1 = models.CharField(max_length=255, blank=True, null=True)
    security_question_2 = models.CharField(max_length=255, blank=True, null=True)
    security_answer_2 = models.CharField(max_length=255, blank=True, null=True)
    security_question_3 = models.CharField(max_length=255, blank=True, null=True)
    security_answer_3 = models.CharField(max_length=255, blank=True, null=True)

    security_questions_set = models.BooleanField(default=False) 

    # Add or update related_name for groups and user_permissions to avoid clashes
    groups = models.ManyToManyField(
        Group,
        verbose_name=('groups'),
        blank=True,
        help_text=(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="customuser_set",
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=('user permissions'),
        blank=True,
        help_text=('Specific permissions for this user.'),
        related_name="customuser_set",
        related_query_name="customuser",
    )

    def __str__(self):
        return self.username
    
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('general', 'General Announcement'),
        ('alert', 'Urgent Alert'),
        ('event', 'Event Reminder'),
        ('action', 'Action Required'),
        ('holiday', 'Holiday Notice'), # Added a common type for schools
    ]

    title = models.CharField(max_length=255, help_text="A brief, descriptive title for the notification.")
    message = models.TextField(help_text="The full content of the notification.")
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='general',
        help_text="Categorize the notification (e.g., General, Urgent)."
    )

    notify_from = models.CharField(
        max_length=100,
        blank=True, # Allow this field to be empty
        null=True,  # Allow NULL in the database
        default="School Administration", # A good default if nothing is specified
        help_text="Who is sending this notification (e.g., Headteacher, Academic Office, System)."
    )

    published_date = models.DateTimeField(
        default=timezone.now,
        help_text="The date and time this notification becomes visible."
    )
    # No 'created_by' field, as per your request.

    class Meta:
        ordering = ['-published_date'] # Order by most recent first
        verbose_name = "School Notification"
        verbose_name_plural = "School Notifications"

    def __str__(self):
        return self.title

    def get_tag_class(self):
        # Helper method to return Bootstrap badge classes based on notification_type
        if self.notification_type == 'general':
            return 'bg-info text-white'
        elif self.notification_type == 'alert':
            return 'bg-danger text-white'
        elif self.notification_type == 'event':
            return 'bg-warning text-dark'
        elif self.notification_type == 'action':
            return 'bg-primary text-white'
        elif self.notification_type == 'holiday':
            return 'bg-success text-white' # Green for holidays
        return 'bg-secondary text-white' # Default fallback

class Document(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/') # Requires Pillow for image processing and file handling
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-uploaded_at']

class CalendarNote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note for {self.date} by {self.user.get_full_name()}"
