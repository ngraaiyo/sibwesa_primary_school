from django import forms
from students.models import Examination  # Correct import for the model

class ExaminationSelectionForm(forms.Form):
    examination = forms.ModelChoiceField(
        queryset=Examination.objects.all().order_by('-date'),
        empty_label="Select an Examination",
        label="Select Exam"
    )