# students/models.py

from django.db import models
from users.models import CustomUser
from django.contrib.auth.models import User
from datetime import date

User.add_to_class('is_head_teacher', models.BooleanField(default=False))

class Class(models.Model):
    name = models.CharField(max_length=100, unique=True)
    class_teacher = models.OneToOneField(
        CustomUser,
        on_delete=models.SET_NULL,
        limit_choices_to={'role': 'class_teacher'},
        null=True,
        blank=True,
        related_name='assigned_class'
    )
    year = models.IntegerField(default=2025)
    # ADD THIS LINE: Many-to-Many relationship with Subject
    subjects = models.ManyToManyField('Subject', related_name='classes_assigned') # Renamed related_name for clarity

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Classes'
        unique_together = ('name', 'year')

class Student(models.Model):
    prem_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True) # <<< ADDED THIS LINE
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender_choices = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    gender = models.CharField(max_length=1, choices=gender_choices)
    
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Graduated', 'Graduated'),
        ('Transferred', 'Transferred Out'),
        ('Suspended', 'Suspended'), # Add other relevant statuses
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Active' # Set a default for new students
    )
    
    current_class = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
    )

    graduation_year = models.IntegerField(null=True, blank=True)

    has_attempted_exam = models.BooleanField(default=False)

    def __str__(self):
        # Update the string representation to include middle name if it exists
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name} ({self.prem_number})"
        return f"{self.first_name} {self.last_name} ({self.prem_number})"
    
    def get_full_name(self):
        """
        Returns the student's full name, including middle name if present.
        """
        full_name_parts = [self.first_name]
        if self.middle_name:
            full_name_parts.append(self.middle_name)
        full_name_parts.append(self.last_name)
        return " ".join(filter(None, full_name_parts)).strip() # .strip() to remove any leading/trailing spaces

    def save(self, *args, **kwargs):
        # If student is set to Graduated but graduation_year is not filled
        if self.status == 'Graduated' and not self.graduation_year:
            self.graduation_year = date.today().year
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['current_class__name', 'first_name', 'last_name']

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    # No direct field linking to Class here, as the M2M is on Class

    def __str__(self):
        return self.name

class Examination(models.Model):
    TERM_CHOICES = [
        ('1', 'Term 1'),
        ('2', 'Term 2'),
        ('3', 'Term 3'),
    ]

    # --- NEW ADDITION FOR EXAM NAMES ---
    EXAM_NAME_CHOICES = [
        ('First Midterm Test', 'First Midterm Test'),
        ('First Term Examination', 'First Term Examination'),
        ('Second Midterm Test', 'Second Midterm Test'),
        ('Annual Examination', 'Annual Examination'),
        ('Mock Examination', 'Mock Examination'),
    ]
    # --- END NEW ADDITION ---

    # Corrected 'name' field to use the new choices
    name = models.CharField(max_length=255, choices=EXAM_NAME_CHOICES) # This is the main change

    date = models.DateField()
    academic_year = models.IntegerField()
    term = models.CharField(max_length=1, choices=TERM_CHOICES)

    classes_taking_exam = models.ManyToManyField('Class', related_name='examinations')

    def __str__(self):
        # Use get_name_display() to show the full name from choices
        return f"{self.get_name_display()} ({self.get_term_display()} - {self.academic_year})"

    class Meta:
        unique_together = ('name', 'academic_year', 'term')
        ordering = ['-academic_year', 'term', 'date', 'name']
class Mark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE)
    # CHANGE THIS LINE from DecimalField to IntegerField
    score = models.IntegerField(null=True, blank=True) # Allow null if no score yet, blank for forms

    def __str__(self):
        return f"{self.student.first_name}'s {self.subject.name} score in {self.examination.name}: {self.score}"

    class Meta:
        unique_together = ('student', 'subject', 'examination')
        ordering = ['examination__academic_year', 'examination__term', 'student__current_class__name', 'student__first_name']

class SchoolDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('poster', 'Poster'),
        ('announcement', 'Announcement'),
        ('link', 'Important Link'),
        ('other', 'Other Document'),
    ]

    title = models.CharField(max_length=255)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES, default='announcement')
    # For text-based content like announcements
    content = models.TextField(blank=True, null=True)
    # For file uploads (e.g., PDF poster, image)
    file = models.FileField(upload_to='school_documents/', blank=True, null=True)
    # For external links
    external_url = models.URLField(max_length=500, blank=True, null=True)
    # Date of publication/upload
    published_date = models.DateTimeField(auto_now_add=True)
    # Whether it's currently active/visible
    is_active = models.BooleanField(default=True)
    # Optional: Link to who published it
    # published_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)

    description = models.TextField(blank=True, null=True, help_text="Optional description for the document.")

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-published_date']
        verbose_name = "School Document"
        verbose_name_plural = "School Documents"
