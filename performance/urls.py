# performance/urls.py
from django.urls import path
from .views import PerformanceAnalysisView, OverallSchoolPerformanceView

urlpatterns = [
    path('analysis/', PerformanceAnalysisView.as_view(), name='performance_analysis'),
    path('overall-school-performance/', OverallSchoolPerformanceView.as_view(), name='overall_school_performance'),
]