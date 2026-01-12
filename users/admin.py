# users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin # Import the default UserAdmin
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .utils import send_sms_notification
from django.contrib import messages
from .models import Notification

# MERGED CustomUserAdmin Class
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Forms for creation and change
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser

    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_approved', 'phone_number',)
    list_filter = ('role', 'is_active', 'is_approved',)
    search_fields = ('username', 'email', 'phone_number',)

    # fieldsets for editing an existing user
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'role', 'gender', 'phone_number', 'address', 'is_approved')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Security Questions', {'fields': (
            'security_question_1', 'security_answer_1',
            'security_question_2', 'security_answer_2',
            'security_question_3', 'security_answer_3',
        )}),
    )

    # add_fieldsets for creating a new user
    add_fieldsets = (
        (None, {'fields': ('username', 'password', 'password2')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'role', 'gender', 'phone_number', 'address', 'is_approved')}),
    )

    def save_model(self, request, obj, form, change):
        # Your save_model logic here
        if change and 'is_active' in form.changed_data and obj.is_active:
             if obj.phone_number:
                 message = f"Hello {obj.username}, your Sibwesa Primary School account has been approved. You can now log in."
                 # Call the function from your utils module
                 # if send_sms_notification(obj.phone_number, message):
                 #     messages.success(request, f"SMS notification sent to {obj.phone_number} for account approval.")
                 # else:
                 #     messages.error(request, f"Failed to send SMS notification to {obj.phone_number}.")
             else:
                 messages.warning(request, f"User {obj.username} approved, but no phone number provided for SMS notification.")
        
        super().save_model(request, obj, form, change)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'published_date')
    list_filter = ('notification_type', 'published_date')
    search_fields = ('title', 'message', 'notify_from')
    date_hierarchy = 'published_date'

