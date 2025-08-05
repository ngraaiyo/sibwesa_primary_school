# users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin # Import the default UserAdmin
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .utils import send_sms_notification
from django.contrib import messages
from .models import Notification

# MERGED CustomUserAdmin Class
class CustomUserAdmin(UserAdmin):
    # Forms for creation and change
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser 

    list_display = UserAdmin.list_display + ('role', 'is_active', 'is_approved', 'phone_number',)

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role', 'is_approved', 'phone_number', 'gender', 'address')}),
        ('Security Questions', {'fields': (
            'security_question_1', 'security_answer_1',
            'security_question_2', 'security_answer_2',
            'security_question_3', 'security_answer_3'
        )}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role', 'is_approved', 'phone_number', 'gender', 'address')}),
    )

    # list_filter: Filters available on the right sidebar in admin
    list_filter = UserAdmin.list_filter + ('role', 'is_approved', 'is_active',)

    # search_fields: Fields searchable via the admin search bar
    search_fields = UserAdmin.search_fields + ('role', 'phone_number',) # Added phone_number

    # Override save_model to send SMS on activation
    def save_model(self, request, obj, form, change):
       
        if change and 'is_active' in form.changed_data and obj.is_active:
            if obj.phone_number:
                message = f"Hello {obj.username}, your Sibwesa Primary School account has been approved. You can now log in."
                if send_sms_notification(obj.phone_number, message):
                    messages.success(request, f"SMS notification sent to {obj.phone_number} for account approval.")
                else:
                    messages.error(request, f"Failed to send SMS notification to {obj.phone_number}.")
            else:
                messages.warning(request, f"User {obj.username} approved, but no phone number provided for SMS notification.")
        
        # Always call the super's save_model to ensure the object is saved correctly
        super().save_model(request, obj, form, change)

admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'published_date')
    list_filter = ('notification_type', 'published_date')
    search_fields = ('title', 'message', 'notify_from')
    date_hierarchy = 'published_date'

