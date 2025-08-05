# users/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from .forms import SetSecurityQuestionsForm, PasswordResetRequestForm, VerifySecurityQuestionsForm
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils.encoding import force_str, force_bytes
from students.models import SchoolDocument
from students.models import Student, Class 
from .models import Notification,Document
from .forms import ProfileEditForm
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import NotificationForm, DocumentForm 

from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from .models import CalendarNote

import requests
import random
import string

from .forms import PasswordResetPhoneForm, SetPasswordSMSForm
from .utils import send_sms_notification, send_admin_new_user_notification_email, send_admin_new_user_notification_sms

CustomUser = get_user_model()

def is_headteacher_or_admin(user):
    return user.is_authenticated and (user.role == 'headteacher' or user.role == 'admin')


def is_teacher(user):
    return user.is_authenticated and user.role in ['academic_teacher', 'class_teacher', 'headteacher', 'statistic_teacher', 'subject_teacher']

@login_required
def teacher_dashboard(request):
    allowed_roles = ['academic_teacher', 'class_teacher', 'headteacher', 'statistic_teacher', 'subject_teacher']
    if request.user.role not in allowed_roles:
        messages.error(request, "You are not authorized to view this page.")
        return redirect('login')

    # Fetch total students for the entire school
    total_students_overall = Student.objects.count()
    total_boys_overall = Student.objects.filter(gender='M').count()
    total_girls_overall = Student.objects.filter(gender='F').count()

    teacher_boys_count = 0
    teacher_girls_count = 0
    assigned_classes = Class.objects.none()

    if request.user.role == 'class_teacher':
        # For a Class Teacher, get stats for their assigned class(es)
        assigned_classes = Class.objects.filter(class_teacher=request.user)
        if assigned_classes.exists():
            students_in_teacher_classes = Student.objects.filter(current_class__in=assigned_classes)
            teacher_boys_count = students_in_teacher_classes.filter(gender='M').count()
            teacher_girls_count = students_in_teacher_classes.filter(gender='F').count()
        else:
            messages.info(request, "You are a Class Teacher but are not currently assigned to any class.")

    elif request.user.role in ['academic_teacher', 'headteacher', 'statistic_teacher']:
        teacher_boys_count = total_boys_overall
        teacher_girls_count = total_girls_overall

    recent_notifications = Notification.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')[:5]

    school_documents = SchoolDocument.objects.filter(is_active=True).order_by('-published_date')[:5]
    if not school_documents.exists():
        print("DEBUG: school_documents QuerySet is EMPTY or contains no active documents.")

    context = {
        'school_documents': school_documents,
        'notifications': recent_notifications,
        'total_boys': total_boys_overall,  # Use the actual calculated value
        'total_girls': total_girls_overall, # Use the actual calculated value
        'teacher_class_boys': teacher_boys_count,
        'teacher_class_girls': teacher_girls_count,
        'assigned_classes': assigned_classes, 
        'page_heading': 'Teacher Dashboard Overview',
    }
    return render(request, 'users/teacher_dashboard.html', context)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False # Set to inactive, requires admin approval
            user.save()

            # --- Send Admin Email and SMS Notifications ---
            email_success = send_admin_new_user_notification_email(user)
            sms_success = send_admin_new_user_notification_sms(user)

            # Provide feedback to the registering user
            if email_success and sms_success:
                messages.success(request, 'Your account has been created successfully and is awaiting admin approval. You will be notified via SMS once approved. Admin has been notified via email and SMS.')
            elif email_success:
                messages.success(request, 'Your account has been created successfully and is awaiting admin approval. You will be notified via SMS once approved. Admin has been notified via email (SMS failed).')
            elif sms_success:
                messages.success(request, 'Your account has been created successfully and is awaiting admin approval. You will be notified via SMS once approved. Admin has been notified via SMS (Email failed).')
            else:
                messages.warning(request, 'Your account has been created successfully and is awaiting admin approval. You will be notified via SMS once approved. Admin notification failed for both email and SMS. Please contact support if you experience delays.')

            return redirect('login') # Redirect to the login page
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()

    context = {
        'form': form,
        'title': 'Register'
    }
    return render(request, 'users/register.html', context)

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active and user.is_approved:
                    login(request, user)
                    messages.success(request, f"Welcome back, {username}!")

                    # --- ADDED/CORRECTED LOGIC FOR SECURITY QUESTIONS REDIRECTION ---
                    # Check if security questions are NOT set
                    if not user.security_questions_set:
                        messages.info(request, "Please set your security questions to complete your account setup.")
                        return redirect('set_security_questions') # Redirect to the set security questions page
                    # --- END OF ADDED/CORRECTED LOGIC ---
                    
                    if user.role == 'admin':
                        return redirect('admin_dashboard')
                    elif user.role in ['academic_teacher', 'class_teacher', 'headteacher', 'statistic_teacher', 'subject_teacher']:
                        return redirect('teacher_dashboard')
                elif not user.is_approved:
                    messages.error(request, "Your account is awaiting admin approval.")
                else:
                    messages.error(request, "Your account is inactive. Please contact administrator.")
            else:
                messages.error(request,"Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        messages.error(request, "You are not authorized to view this page.")
        return redirect('login')
    return render(request, 'users/admin_dashboard.html')

@login_required
def home_view(request):
    if request.user.is_authenticated:
        if request.user.role == 'admin':
            return redirect('admin_dashboard')
        elif request.user.role in ['academic_teacher', 'class_teacher', 'headteacher', 'statistic_teacher', 'subject_teacher']:
            return redirect('teacher_dashboard')
    messages.warning(request, "Your role does not have a designated dashboard, or your account is not yet active/approved.")
    return redirect('login')

@login_required
def set_security_questions(request):
    user = request.user # Get the currently logged-in user

    if request.method == 'POST':
        form = SetSecurityQuestionsForm(request.POST, instance=user)
        if form.is_valid():
            form.save() # The save method in the form handles hashing
            # Also set the flag on the user model directly if not handled in form.save()
            user.security_questions_set = True
            user.save()
            messages.success(request, 'Your security questions have been set successfully.')
            return redirect('home')
        else:
           messages.error(request, 'Please correct the errors below.')
    else:
        form = SetSecurityQuestionsForm(instance=user)
    
    context = {
        'form': form,
        'title': 'Set Security Questions'
    }
    return render(request, 'users/set_security_questions.html', context)

def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            # The user object is attached to the form by its clean_identifier method
            user = form.user 
            
            # Store the user's ID in the session to carry it to the next step
            request.session['password_reset_user_id'] = user.id
            
            messages.info(request, "Please answer your security questions to proceed.")
            # Redirect to the view that verifies security questions
            return redirect('verify_security_questions') # Removed reverse() and 'users:'
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordResetRequestForm()
    
    context = {
        'form': form,
        'title': 'Password Reset Request'
    }
    return render(request, 'users/password_reset_request.html', context)

def send_sms(phone_number, message):
    if not settings.AFRICAS_TALKING_API_KEY or not settings.AFRICAS_TALKING_USERNAME:
        print("Africa's Talking API keys not set in settings.py. SMS will not be sent.")
        return False

    url = "https://api.africastalking.com/version1/messaging"
    headers = {
        "Accept": "application/json",
        "Apikey": settings.AFRICAS_TALKING_API_KEY
    }
    data = {
        "username": settings.AFRICAS_TALKING_USERNAME,
        "to": phone_number,
        "message": message
    }
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        print("SMS response:", response.json())
        if response.json().get('SMSMessageData', {}).get('Recipients')[0].get('status') == 'Success':
            return True
        else:
            print("SMS sending failed:", response.json())
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error sending SMS: {e}")
        return False

def password_reset_request_sms(request):
    if request.method == 'POST':
        form = PasswordResetPhoneForm(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data['phone_number']
            user = CustomUser.objects.get(phone_number=phone_number)

            otp = ''.join(random.choices(string.digits, k=6))
            
            request.session['password_reset_otp'] = otp
            request.session['password_reset_user_id'] = user.pk
            request.session.set_expiry(300) # OTP valid for 5 minutes (300 seconds)

            message = f"Your password reset code is: {otp}. It expires in 5 minutes."
            if send_sms(phone_number, message):
                return redirect('password_reset_confirm_sms') # Removed 'users:'
            else:
                messages.error(request, 'Failed to send SMS. Please try again later.')
    else:
        form = PasswordResetPhoneForm()
    return render(request, 'users/password_reset_request_sms.html', {'form': form})

def password_reset_confirm_sms(request):
    user_id = request.session.get('password_reset_user_id')
    otp_from_session = request.session.get('password_reset_otp')

    if not user_id or not otp_from_session:
        messages.error(request, 'Password reset session expired or invalid. Please request a new one.')
        return redirect('password_reset_sms_request') # Removed 'users:'
        
    user = get_object_or_404(CustomUser, pk=user_id)

    if request.method == 'POST':
        form = SetPasswordSMSForm(request.POST)
        if form.is_valid():
            sms_code = form.cleaned_data['sms_code']
            new_password = form.cleaned_data['new_password1']

            if sms_code == otp_from_session:
                user.password = make_password(new_password)
                user.save()
                messages.success(request, 'Your password has been reset successfully. You can now log in.')
                del request.session['password_reset_otp']
                del request.session['password_reset_user_id']
                return redirect('login') # Removed 'users:'
            else:
                messages.error(request, 'Invalid SMS verification code.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SetPasswordSMSForm()
    return render(request, 'users/password_reset_confirm_sms.html', {'form': form, 'user': user})

def verify_security_questions(request):
    user_id = request.session.get('password_reset_user_id')

    if not user_id:
        messages.error(request, 'Password reset session expired or invalid. Please start again.')
        return redirect('password_reset') # Removed 'users:'

    user = get_object_or_404(CustomUser, pk=user_id)

    if request.method == 'POST':
        form = VerifySecurityQuestionsForm(request.POST, user=user)
        if form.is_valid():
            messages.success(request, 'Security questions verified. A password reset code has been sent to your phone number.')
            
            otp = ''.join(random.choices(string.digits, k=6))
            
            request.session['password_reset_otp'] = otp
            request.session.set_expiry(300)

            message = f"Your password reset code is: {otp}. It expires in 5 minutes."
            if send_sms(user.phone_number, message):
                return redirect('password_reset_confirm_sms') # Removed 'users:'
            else:
                messages.error(request, 'Failed to send SMS. Please try again later.')
                return redirect('password_reset') # Removed 'users:'
        else:
            messages.error(request, 'Incorrect answers to security questions. Please try again.')
    else:
        form = VerifySecurityQuestionsForm(user=user)
    
    context = {
        'form': form,
        'user': user,
        'title': 'Verify Security Questions'
    }
    return render(request, 'users/verify_security_questions.html', context)

@login_required
@user_passes_test(is_headteacher_or_admin)
def all_teachers_view(request):
    """
    Displays a list of all users who have a 'teacher' role.
    You might need to adjust the `teacher_roles` list based on your actual roles.
    """
    teacher_roles = ['academic_teacher', 'class_teacher', 'subject_teacher', 'statistic_teacher']
    teachers = CustomUser.objects.filter(role__in=teacher_roles).order_by('first_name', 'last_name')
    teacher_count = teachers.count()

    context = {
        'page_heading': 'All Teachers',
        'teachers': teachers,
        'teacher_count': teacher_count,
    }
    return render(request, 'users/all_teachers.html', context)

@login_required
@user_passes_test(is_headteacher_or_admin, login_url='/login/')
def edit_teacher_view(request, pk): # <--- This function MUST exist
    """
    Handles editing existing teacher accounts.
    """
    teacher = get_object_or_404(CustomUser, pk=pk) # Make sure CustomUser is imported

    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=teacher) # Make sure CustomUserChangeForm is imported
        if form.is_valid():
            form.save()
            messages.success(request, f"Teacher {teacher.first_name} {teacher.last_name} updated successfully.")
            return redirect('all_teachers')
        else:
            messages.error(request, 'Error updating teacher. Please correct the form errors.')
    else:
        form = CustomUserChangeForm(instance=teacher)

    context = {
        'page_heading': f'Edit Teacher: {teacher.first_name} {teacher.last_name}',
        'form': form,
        'teacher': teacher,
    }
    return render(request, 'users/edit_teacher.html', context)

@login_required
@user_passes_test(is_headteacher_or_admin)
def add_teacher_view(request):
    """
    Handles adding new teacher accounts.
    You should use a form that is appropriate for creating your CustomUser model,
    and potentially pre-set the 'role' field or make it selectable.
    """
    if request.method == 'POST':
        # Replace CustomUserCreationForm with your actual user creation/teacher form
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # You might want to default the role to a teacher role here if not handled by the form
            # user.role = 'academic_teacher' # Example
            user.save()
            messages.success(request, f"Teacher {user.first_name or user.username} added successfully.")
            return redirect('all_teachers') # Redirect to the list of teachers
    else:
        form = CustomUserCreationForm() # Replace with your actual user creation/teacher form

    context = {
        'page_heading': 'Add New Teacher',
        'form': form,
    }
    return render(request, 'users/add_teacher.html', context)

@login_required
@user_passes_test(is_headteacher_or_admin, login_url='/login/')
def delete_teacher_view(request, pk):
    """
    Handles deleting a teacher account.
    Only allows POST requests to prevent accidental deletion via GET.
    """
    teacher = get_object_or_404(CustomUser, pk=pk)

    if request.method == 'POST':
        teacher_name = f"{teacher.first_name} {teacher.last_name}" if teacher.first_name and teacher.last_name else teacher.username
        teacher.delete()
        messages.success(request, f"Teacher '{teacher_name}' deleted successfully.")
        return redirect('all_teachers')
    else:
        messages.error(request, "Invalid request method for deleting a teacher.")
        return redirect('all_teachers')

@login_required
def profile_view(request):
    """
    Renders the user's profile page.
    """
    context = {
        'user': request.user,
        # 'user_profile': user_profile,
    }
    return render(request, 'users/profile.html', context)

@login_required
def profile_edit_view(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('profile') # Redirect to the profile display page
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = ProfileEditForm(instance=user) # Pre-populate the form with current user data

    context = {
        'form': form,
        'page_heading': 'Edit Profile' # For the base.html block
    }
    return render(request, 'users/profile_edit.html', context)

@login_required
@require_POST
def save_calendar_note(request):
    try:
        # Use json.loads if the data is sent as a JSON body (recommended for AJAX)
        data = json.loads(request.body)
        note_date = data.get('date')
        note_content = data.get('content')

        if not note_date or not note_content:
            return JsonResponse({'error': 'Date and content are required.'}, status=400)

        CalendarNote.objects.create(
            user=request.user,
            date=note_date,
            content=note_content
        )
        return JsonResponse({'message': 'Note saved successfully!'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff # or self.request.user.is_superuser if only superusers

# List all notifications
class NotificationListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Notification
    template_name = 'users/notification_list.html'
    context_object_name = 'notifications'
    ordering = ['-timestamp'] # Order by newest first

# Create a new notification
class NotificationCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Notification
    form_class = NotificationForm
    template_name = 'users/notification_form.html'
    success_url = reverse_lazy('notification_list')

    def form_valid(self, form):
        form.instance.sender = self.request.user # Assuming the logged-in user is the sender
        return super().form_valid(form)

# Update an existing notification
class NotificationUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Notification
    form_class = NotificationForm
    template_name = 'users/notification_form.html'
    context_object_name = 'notification'
    success_url = reverse_lazy('notification_list')

class NotificationDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    model = Notification
    template_name = 'users/notification_detail.html' # You'll need to create this template
    context_object_name = 'notification'

# Delete a notification
class NotificationDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Notification
    template_name = 'users/notification_confirm_delete.html'
    context_object_name = 'notification'
    success_url = reverse_lazy('notification_list')

class NotificationListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Notification
    template_name = 'users/notification_list.html'
    context_object_name = 'notifications'
    ordering = ['-published_date']

class DocumentCreateView(LoginRequiredMixin, CreateView): # Add AdminRequiredMixin if only admins can upload
    model = Document
    form_class = DocumentForm # Use the DocumentForm we defined
    template_name = 'users/document_form.html'
    success_url = reverse_lazy('document_list') # Redirect to the document list after successful upload

    def form_valid(self, form):
        # Automatically set the 'uploaded_by' field to the current user
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)

class DocumentDetailView(LoginRequiredMixin, DetailView): # Decide if AdminRequiredMixin is needed
    model = Document
    template_name = 'users/document_detail.html' # Create this template
    context_object_name = 'document'

class DocumentUpdateView(LoginRequiredMixin, UpdateView): # Add AdminRequiredMixin if only admins can edit
    model = Document
    form_class = DocumentForm
    template_name = 'users/document_form.html'
    context_object_name = 'document' # Standard practice for UpdateView
    success_url = reverse_lazy('document_list')

class DocumentDeleteView(LoginRequiredMixin, DeleteView): # Decide if AdminRequiredMixin is needed
    model = Document
    template_name = 'users/document_confirm_delete.html' # Create this template
    context_object_name = 'document'
    success_url = reverse_lazy('document_list')

class DocumentListView(LoginRequiredMixin, ListView): # Decide if AdminRequiredMixin is needed
    model = Document
    template_name = 'users/document_list.html' # Create this template
    context_object_name = 'documents'
    ordering = ['-uploaded_at']

# Notification views
notification_list = NotificationListView.as_view()
notification_create = NotificationCreateView.as_view()
notification_update = NotificationUpdateView.as_view()
notification_delete = NotificationDeleteView.as_view()
notification_detail = NotificationDetailView.as_view() # Ensure this is present and correct

# NEW: Document views
document_list = DocumentListView.as_view()
document_create = DocumentCreateView.as_view()
document_detail = DocumentDetailView.as_view()
document_update = DocumentUpdateView.as_view()
document_delete = DocumentDeleteView.as_view()
