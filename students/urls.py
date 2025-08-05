# students/urls.py

from django.urls import path, include
from . import views

urlpatterns = [
    path('students/add/', views.student_add, name='student_add'),
    path('students/edit/<int:pk>/', views.student_edit, name='student_edit'),
    path('students/delete/<int:pk>/', views.student_delete, name='student_delete'),
    path('students/upload-excel/', views.student_upload_excel, name='student_upload_excel'),
    path('students/my-class/', views.students_in_my_class_view, name='students_in_my_class'),
    path('students/all/', views.all_students_view, name='all_students'),

    # Class Management URLs
    path('classes/', views.class_list, name='class_list'),
    path('classes/add/', views.class_add, name='class_add'),
    path('classes/edit/<int:pk>/', views.class_edit, name='class_edit'),
    path('classes/delete/<int:pk>/', views.class_delete, name='class_delete'),

     # --- ADD THESE PLACEHOLDER URLS ---
    path('examinations/', views.examination_list, name='examination_list'),
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/add/', views.subject_add, name='subject_add'),
    path('subjects/edit/<int:pk>/', views.subject_edit, name='subject_edit'),
    path('subjects/delete/<int:pk>/', views.subject_delete, name='subject_delete'),

    # Examination Management URLs
    path('examinations/', views.examination_list, name='examination_list'),
    path('examinations/add/', views.examination_add, name='examination_add'),
    path('examinations/edit/<int:pk>/', views.examination_edit, name='examination_edit'),
    path('examinations/delete/<int:pk>/', views.examination_delete, name='examination_delete'),

     # Mark Entry URLs
    path('marks/entry-selection/', views.mark_entry_selection, name='mark_entry_selection'),
    path('marks/upload-excel/', views.mark_excel_upload, name='mark_excel_upload'),
    path('marks/list/', views.mark_list, name='mark_list'),
    path('marks/entry/<int:exam_id>/<int:subject_id>/<int:class_id>/', views.mark_entry_form, name='mark_entry_form'),
     
     # Results URLs
    path('results/selection/', views.result_selection, name='result_selection'),
    path('results/class-summary/', views.class_results_summary, name='class_results_summary'),
    path('results/<int:exam_id>/student/<int:student_id>/', views.student_result_slip, name='student_result_slip'),

     # URL for selecting class and exam for performance analysis
    path('performance/select/', views.performance_selection_view, name='performance_selection'),
    path('class/<int:class_id>/examination/<int:exam_id>/performance-analysis/', views.class_performance_analysis_view, name='class_performance_analysis'),
    path('class/<int:class_id>/examination/<int:exam_id>/results-summary/', views.class_results_summary_view, name='class_results_summary'),

    # Timetable & Attendance URLs (Placeholders for now)
    path('attendance/', views.attendance_view, name='attendance_view'), 
    path('timetable/', views.timetable_view, name='timetable_view'),

    # Student Management
    path('students/add/', views.add_student, name='add_student'), 
    path('students/edit/<int:pk>/', views.edit_student, name='edit_student'),

    path('class-summary-pdf/<int:exam_id>/<int:class_id>/', views.download_class_summary_pdf, name='class_summary_pdf'),
    path('student-result-pdf/<int:exam_id>/<int:student_id>/',views.download_student_result_pdf,name='student_result_pdf'),

    path('upload-excel/', views.upload_students_excel, name='upload_students_excel'),
]