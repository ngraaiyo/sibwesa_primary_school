# reports/urls.py

from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
# General Reports
path('class-performance/', views.class_performance_summary, name='class_performance_summary'),
path('teachers/', views.teachers_registered, name='teachers_registered'),
path('graduates/', views.graduated_students, name='graduated_students'),
path('select-class/<str:report_type>/', views.select_class_for_report, name='select_class_for_report'),

# --- TOP AND BOTTOM STUDENTS REPORTS ---
path('select-exam-for-top-bottom/', views.select_exam_for_top_bottom, name='select_exam_for_top_bottom'),
path('select-class-for-top-bottom/<int:examination_id>/', views.select_class_for_top_bottom, name='select_class_for_top_bottom'),
path('top-bottom-students/<int:class_id>/<int:examination_id>/',views.top_and_bottom_students, name='top_and_bottom_students'),
path('top-bottom-pdf/<int:class_id>/<int:examination_id>/',views.top_bottom_pdf, name='top_bottom_pdf'),

# --- NOT ATTEMPTED STUDENTS REPORTS ---
path('select-exam-for-not-attempted/', views.select_exam_for_not_attempted, name='select_exam_for_not_attempted'),
path("overall-report/<int:examination_id>/", views.overall_report_with_attempt_status, name="overall_report_with_attempt_status"),
path('not-attempted-students/<int:class_id>/<int:examination_id>/', views.not_attempted_students, name='not_attempted_students'),

# --- STUDENT PERFORMANCE REPORTS ---
path('student/trend/<int:student_id>/', views.student_performance_trend, name='student_performance_trend'),
path('select-comparison-exam/', views.select_comparison_exam, name='select_comparison_exam'),
path('handle-comparison/', views.handle_comparison_selection, name='handle_comparison_selection'),
path('class/comparison/<int:examination_id>/', views.class_comparison, name='class_comparison'),
]