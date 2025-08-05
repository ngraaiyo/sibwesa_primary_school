# users/urls.py

from django.urls import path
from . import views # Import views from the current app
from django.contrib.auth import views as auth_views # Import Django's default auth views for login/logout (optional, but good for password reset etc.)


urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'), # Using our custom login view
    path('logout/', views.user_logout, name='logout'), # Using our custom logout view
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('teacher_dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),

    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='users/password_change_form.html',
        success_url='/users/password-change/done/' # Or use reverse_lazy('password_change_done')
    ), name='password_change'), # <-- ADD THIS LINE

    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='users/password_change_done.html'
    ), name='password_change_done'),

    # Teacher Management URLs
    path('teachers/', views.all_teachers_view, name='all_teachers'),
    path('teachers/add/', views.add_teacher_view, name='add_teacher'),
    path('teachers/edit/<int:pk>/', views.edit_teacher_view, name='edit_teacher'),
    path('teachers/delete/<int:pk>/', views.delete_teacher_view, name='delete_teacher'),

    path('verify_security_questions/<int:user_id>/', views.verify_security_questions, name='verify_security_questions'),
    path('set_security_questions/', views.set_security_questions, name='set_security_questions'),

    path('password_reset/', views.password_reset_request_sms, name='password_reset'),
    path('password-reset-confirm-sms/', views.password_reset_confirm_sms, name='password_reset_confirm_sms'),
   
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/create/', views.notification_create, name='notification_create'),
    path('notifications/<int:pk>/', views.notification_detail, name='notification_detail'),
    path('notifications/<int:pk>/edit/', views.notification_update, name='notification_update'),
    path('notifications/<int:pk>/delete/', views.notification_delete, name='notification_delete'),

    # NEW: Document URLs
    path('documents/', views.document_list, name='document_list'),
    path('documents/upload/', views.document_create, name='document_upload'), # Using 'upload' for clarity
    path('documents/<int:pk>/', views.document_detail, name='document_detail'),
    path('documents/<int:pk>/edit/', views.document_update, name='document_update'),
    path('documents/<int:pk>/delete/', views.document_delete, name='document_delete'),


    path('documents/', views.document_list, name='document_list'),
    path('documents/upload/', views.document_create, name='document_upload'),
    path('documents/<int:pk>/', views.document_detail, name='document_detail'),
    path('documents/<int:pk>/edit/', views.document_update, name='document_update'),
    path('documents/<int:pk>/delete/', views.document_delete, name='document_delete'),
    path('save-note/', views.save_calendar_note, name='save_calendar_note'),
]       