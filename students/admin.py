# students/admin.py

from django.contrib import admin
from .models import SchoolDocument,Student, Class, Subject, Examination, Mark

# Register your models here
admin.site.register(Student)
admin.site.register(Class)
admin.site.register(Subject)
admin.site.register(Examination)
admin.site.register(Mark)
@admin.register(SchoolDocument)
class SchoolDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'document_type', 'published_date', 'is_active')
    list_filter = ('document_type', 'is_active')
    search_fields = ('title', 'content')