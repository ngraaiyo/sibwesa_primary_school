# students/forms.py

from django import forms
from .models import Student, Class, Subject, Examination, Mark
from users.models import CustomUser
from django.contrib import messages
from .models import SchoolDocument


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__' # Or your specific fields like ['first_name', 'last_name', ...]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), # Added type='date' for browser date picker
            'gender': forms.Select(attrs={'class': 'form-select'}), # Use form-select for select inputs
            'admission_number': forms.TextInput(attrs={'class': 'form-control'}),
            'current_class': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class ClassForm(forms.ModelForm):
    class_teacher = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role='class_teacher', is_approved=True, is_active=True),
        required=False,  
        empty_label="No Class Teacher Assigned"
    )

    class Meta:
        model = Class
        fields = ['name', 'year', 'class_teacher']
        widgets = {
            'year': forms.NumberInput(attrs={'min': '2000', 'max': '2100'}), # Example for year
        }

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code']

class ExaminationForm(forms.ModelForm):
    class Meta:
        model = Examination
        fields = ['name', 'date', 'academic_year', 'term']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'academic_year': forms.NumberInput(attrs={'min': '2000', 'max': '2100'}),
        }

class MarkEntrySelectionForm(forms.Form):
    examination = forms.ModelChoiceField(
        queryset=Examination.objects.all().order_by('-academic_year', 'term', 'date', 'name'),
        empty_label="--- Select Examination ---",
        label="Select Examination"
    )

    class_name = forms.ModelChoiceField(
        queryset=Class.objects.all().order_by('name'),
        empty_label="--- Select Class ---",
        required=False, 
        label="Select Class"
    )

    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all().order_by('name'),
        empty_label="--- Select Subject ---",
        label="Select Subject"
    )

class MarkExcelUploadForm(forms.Form):
    excel_file = forms.FileField(
        label="Select Excel File (.xlsx)",
        help_text="Upload an Excel file with columns: Admission_Number, Subject_Code, Score"
    )

class MarkEntrySelectionForm(forms.Form):
    examination = forms.ModelChoiceField(
        queryset=Examination.objects.all().order_by('-academic_year', 'term', 'date', 'name'),
        empty_label="--- Select Examination ---",
        label="Select Examination"
    )

    class_name = forms.ModelChoiceField(
        queryset=Class.objects.all().order_by('name'),
        empty_label="--- Select Class ---",
        required=False,
        label="Select Class"
    )

    subject = forms.ModelChoiceField( 
        queryset=Subject.objects.all().order_by('name'),
        empty_label="--- Select Subject (Optional for Overview) ---",
        required=False, # <<< CHANGED TO FALSE
        label="Select Subject (for single subject view or mark entry)"
    )

class ResultSelectionForm(forms.Form):
    examination = forms.ModelChoiceField(
        queryset=Examination.objects.all().order_by('-academic_year', 'term', 'date', 'name'),
        empty_label="--- Select Examination ---",
        label="Select Examination"
    )
    class_name = forms.ModelChoiceField(
        queryset=Class.objects.all().order_by('name'),
        empty_label="--- Select Class ---",
        required=False,
        label="Select Class"
    )

class StudentCreationForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['first_name', 'middle_name', 'last_name', 'date_of_birth', 'gender', 'admission_number', 'current_class']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) # Pop the user
        super().__init__(*args, **kwargs)

        if user and user.role == 'class_teacher':
            try:
                assigned_class = Class.objects.get(class_teacher=user)
                self.fields['current_class'].queryset = Class.objects.filter(pk=assigned_class.pk)
                self.fields['current_class'].initial = assigned_class.pk
                self.fields['current_class'].widget.attrs['readonly'] = True
                self.fields['current_class'].help_text = "Your assigned class."
            except Class.DoesNotExist:
                self.fields['current_class'].queryset = Class.objects.none()
                self.fields['current_class'].help_text = "You are not assigned to a class."
        elif user and user.role == 'academic_teacher':
            # Academic teachers can see all classes but might not be able to edit class
            # if this form is also used for editing by non-admin. Adjust as needed.
            self.fields['current_class'].queryset = Class.objects.all().order_by('name', 'year')
        elif user and user.role == 'admin':
            self.fields['current_class'].queryset = Class.objects.all().order_by('name', 'year')

class StudentExcelUploadForm(forms.Form):
    excel_file = forms.FileField(
        label='Select Excel File',
        help_text='Upload an Excel file (.xlsx or .xls) with student data.',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )

class SchoolDocumentForm(forms.ModelForm):
    class Meta:
        model = SchoolDocument
        fields = ['title', 'description', 'file', 'document_type']
