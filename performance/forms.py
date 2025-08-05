# performance/forms.py
from django import forms
from students.models import Examination 

class PerformanceAnalysisFilterForm(forms.Form):
    examination = forms.ModelChoiceField(
        queryset=Examination.objects.all().order_by('-academic_year', '-term', '-name'),
        empty_label="Select an Examination",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Select Examination for Analysis"
    )