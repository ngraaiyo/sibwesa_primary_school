# students/admin.py

from django.contrib import admin
from .models import Student, Class, Subject, Examination, Mark, SchoolDocument

# Create a custom admin class for Student
class StudentAdmin(admin.ModelAdmin):
    list_display = ('prem_number', 'first_name', 'last_name', 'current_class', 'status')
    list_filter = ('current_class', 'status')
    search_fields = ('prem_number', 'first_name', 'last_name')

# Register your models with their custom admin classes
admin.site.register(Student, StudentAdmin)
admin.site.register(Class)
admin.site.register(Subject)
admin.site.register(Examination)
admin.site.register(Mark)

@admin.register(SchoolDocument)
class SchoolDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'document_type', 'published_date', 'is_active')
    list_filter = ('document_type', 'is_active')
    search_fields = ('title', 'content')