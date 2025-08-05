# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
import hashlib
from .models import Notification, Document
from django.core.validators import RegexValidator

CustomUser = get_user_model()
SECURITY_QUESTIONS_CHOICES = [
    ('', '--- Select a Security Question ---'), # Optional empty choice
    ('What was your childhood nickname?', 'What was your childhood nickname?'),
    ('What is your mother\'s maiden name?', 'What is your mother\'s maiden name?'),
    ('What was the name of your first pet?', 'What was the name of your first pet?'),
    ('In what city were you born?', 'In what city were you born?'),
    ('What is your favorite book?', 'What is your favorite book?'),
    ('Unatoke mkoa gani?', 'Unatokea mkoa gani?'),
    ('Shule ya msingi ulisoma wapi?', 'Shule ya msingi ulisoma wapi?'),
    ('Chuo cha ualimu ulisoma chuo gani?', 'Chuo cha ualimu ulisoma chuo gani?'),
]

class CustomUserCreationForm(UserCreationForm):
    gender = forms.ChoiceField(
        choices=CustomUser.GENDER_CHOICES,
        required=False,
        label="Gender",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        label="Phone Number",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'gender',
            'phone_number',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    

        # This loop applies Bootstrap classes to all fields.
        for field_name, field in self.fields.items():
            if not hasattr(field.widget, 'attrs'):
                field.widget.attrs = {}
            
            if isinstance(field.widget, forms.widgets.TextInput) or \
               isinstance(field.widget, forms.widgets.EmailInput) or \
               isinstance(field.widget, forms.widgets.PasswordInput) or \
               isinstance(field.widget, forms.widgets.Textarea):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.widgets.Select):
                field.widget.attrs.update({'class': 'form-select'})

class CustomUserChangeForm(UserChangeForm):
    gender = forms.ChoiceField(
        choices=CustomUser.GENDER_CHOICES,
        required=False,
        label="Gender",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        label="Phone Number",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = (
            'username', 'first_name', 'last_name', 'email',
            'is_active', 'is_staff', 'is_superuser',
            'groups', 'user_permissions',
            'gender', 'phone_number', 
        )

class TeacherForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'username', 'email',
            'gender',
            'phone_number',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not hasattr(field.widget, 'attrs'):
                field.widget.attrs = {}
            if 'class' not in field.widget.attrs:
                 if isinstance(field.widget, forms.widgets.TextInput) or \
                    isinstance(field.widget, forms.widgets.EmailInput) or \
                    isinstance(field.widget, forms.widgets.PasswordInput) or \
                    isinstance(field.widget, forms.widgets.Textarea):
                    field.widget.attrs.update({'class': 'form-control'})
                 elif isinstance(field.widget, forms.widgets.Select):
                    field.widget.attrs.update({'class': 'form-select'})

class SetSecurityQuestionsForm(forms.ModelForm):
    # Use ChoiceField for questions so users select from predefined options
    security_question_1 = forms.ChoiceField(
        choices=SECURITY_QUESTIONS_CHOICES,
        required=True,
        label="Security Question 1"
    )
    security_answer_1 = forms.CharField(
        max_length=255, 
        required=True, 
        label="Answer 1",
        widget=forms.TextInput(attrs={'placeholder': 'Your answer'})
    )

    security_question_2 = forms.ChoiceField(
        choices=SECURITY_QUESTIONS_CHOICES,
        required=True,
        label="Security Question 2"
    )
    security_answer_2 = forms.CharField(
        max_length=255, 
        required=True, 
        label="Answer 2",
        widget=forms.TextInput(attrs={'placeholder': 'Your answer'})
    )

    security_question_3 = forms.ChoiceField(
        choices=SECURITY_QUESTIONS_CHOICES,
        required=True,
        label="Security Question 3"
    )
    security_answer_3 = forms.CharField(
        max_length=255, 
        required=True, 
        label="Answer 3",
        widget=forms.TextInput(attrs={'placeholder': 'Your answer'})
    )

    class Meta:
        model = CustomUser
        fields = [
            'security_question_1', 'security_answer_1',
            'security_question_2', 'security_answer_2',
            'security_question_3', 'security_answer_3',
        ]
        # We don't want to show raw answers in forms, even for editing
        widgets = {
            'security_answer_1': forms.TextInput(), # This can be hidden if only setting
            'security_answer_2': forms.TextInput(),
            'security_answer_3': forms.TextInput(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate initial values if user already has questions set (for editing)
        if self.instance.pk:
            self.fields['security_answer_1'].initial = '' # Don't show the hashed answer
            self.fields['security_answer_2'].initial = ''
            self.fields['security_answer_3'].initial = ''

    def clean(self):
        cleaned_data = super().clean()
        q1 = cleaned_data.get('security_question_1')
        q2 = cleaned_data.get('security_question_2')
        q3 = cleaned_data.get('security_question_3')

        # Ensure all questions are unique
        questions = [q for q in [q1, q2, q3] if q] # Filter out empty choices if allowed
        if len(set(questions)) != len(questions):
            self.add_error(None, "Security questions must be unique.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
    
        if self.cleaned_data.get('security_answer_1'):
            user.security_answer_1 = hashlib.sha256(self.cleaned_data['security_answer_1'].encode('utf-8')).hexdigest()
        if self.cleaned_data.get('security_answer_2'):
            user.security_answer_2 = hashlib.sha256(self.cleaned_data['security_answer_2'].encode('utf-8')).hexdigest()
        if self.cleaned_data.get('security_answer_3'):
            user.security_answer_3 = hashlib.sha256(self.cleaned_data['security_answer_3'].encode('utf-8')).hexdigest()
        
        if commit:
            user.save()
        return user

class PasswordResetRequestForm(forms.Form):
    identifier = forms.CharField(
        max_length=255,
        required=True,
        label="Username, Email, or Phone Number",
        help_text="Enter your username, registered email, or phone number.",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    def clean_identifier(self):
        identifier = self.cleaned_data['identifier']
        # Lowercase email for case-insensitive lookup
        if '@' in identifier:
            identifier = identifier.lower()

        user_model = get_user_model()

        try:
            user = user_model.objects.get(username__iexact=identifier)
        except user_model.DoesNotExist:
            # Try to find by email
            try:
                user = user_model.objects.get(email__iexact=identifier)
            except user_model.DoesNotExist:
                try:
                    user = user_model.objects.get(phone_number=identifier)
                except user_model.DoesNotExist:
                    raise ValidationError("No user found with that username, email, or phone number.")

        self.user = user 
        return identifier

class VerifySecurityQuestionsForm(forms.Form):
    question_1_text = forms.CharField(widget=forms.HiddenInput(), required=False)
    question_2_text = forms.CharField(widget=forms.HiddenInput(), required=False)
    question_3_text = forms.CharField(widget=forms.HiddenInput(), required=False)

    answer_1 = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'placeholder': 'Your Answer for Q1'}), label="Answer for Q1")
    answer_2 = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'placeholder': 'Your Answer for Q2'}), label="Answer for Q2")
    answer_3 = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'placeholder': 'Your Answer for Q3'}), label="Answer for Q3")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We need to make sure the labels are correctly set from initial data
        if 'initial' in kwargs and 'question_1_text' in kwargs['initial']:
            self.fields['answer_1'].label = kwargs['initial']['question_1_text']
        if 'initial' in kwargs and 'question_2_text' in kwargs['initial']:
            self.fields['answer_2'].label = kwargs['initial']['question_2_text']
        if 'initial' in kwargs and 'question_3_text' in kwargs['initial']:
            self.fields['answer_3'].label = kwargs['initial']['question_3_text']

class PasswordResetPhoneForm(forms.Form):
    phone_number = forms.CharField(
        label="Phone Number",
        max_length=15,
        widget=forms.TextInput(attrs={'placeholder': '+2557XXXXXXXX'})
    )

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        # Basic validation for phone number format (can be more robust)
        if not phone_number.startswith('+') or not phone_number[1:].isdigit():
            raise forms.ValidationError("Please enter a valid phone number, e.g., +2557XXXXXXXX.")
        
        # Check if user with this phone number exists
        if not CustomUser.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError("No user found with this phone number.")
        return phone_number

class SetPasswordSMSForm(forms.Form):
    # This form will be used to enter the SMS code and the new password
    sms_code = forms.CharField(label="SMS Verification Code", max_length=6,
                               widget=forms.TextInput(attrs={'placeholder': 'Enter 6-digit code'}))
    new_password1 = forms.CharField(label="New password", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Confirm new password", widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if new_password1 and new_password2 and new_password1 != new_password2:
            self.add_error('new_password2', "Passwords don't match.")
        return cleaned_data

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'gender', 'phone_number']

class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['title', 'message', 'notification_type', 'notify_from', 'published_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}), # Use 'rows' for textarea height
            'notification_type': forms.Select(attrs={'class': 'form-select'}), # Use 'form-select' for select fields
            'notify_from': forms.TextInput(attrs={'class': 'form-control'}),
            # Note: For datetime-local, the 'type' attribute is important for the browser's native picker
            'published_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'description', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter document title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Optional: Describe the document'}),
            # For FileInput, 'form-control' makes it consistent, though appearance can vary by browser
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

