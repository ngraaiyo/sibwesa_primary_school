# performance/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.db.models.functions import Coalesce
from django.db.models import Avg, F, Count, Q
from students.models import Student, Mark, Class, Subject, Examination # Corrected import
from .forms import PerformanceAnalysisFilterForm # Import your form

class PerformanceAnalysisView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'performance/performance_analysis.html'

    def test_func(self):
        # Allow only Academic Teacher, Statistic Teacher, and Headteacher
        allowed_roles = ['academic_teacher', 'statistic_teacher', 'headteacher']
        return self.request.user.role in allowed_roles

    def get(self, request, *args, **kwargs):
        form = PerformanceAnalysisFilterForm()
        context = {
            'form': form,
            'analysis_data': None,
            'selected_examination': None,
            'page_heading': 'Whole School Performance Analysis'
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = PerformanceAnalysisFilterForm(request.POST)
        analysis_data = []
        selected_examination = None

        if form.is_valid():
            selected_examination = form.cleaned_data['examination']

            # 1. Overall School Averages by Subject for the selected Examination
            overall_subject_averages = Mark.objects.filter(examination=selected_examination) \
                                                    .values('subject__name') \
                                                    .annotate(avg_score=Avg('score')) \
                                                    .order_by('subject__name')

            # 2. Class-wise Averages by Subject for the selected Examination
            class_subject_averages = Mark.objects.filter(examination=selected_examination) \
                                                .values('student__current_class__name', 'subject__name') \
                                                .annotate(avg_score=Avg('score'), student_count=Count('student', distinct=True)) \
                                                .order_by('student__current_class__name', 'subject__name')

            # Re-structure class_subject_averages for easier template rendering
            # { 'ClassName': { 'SubjectName': avg_score, ... }, ... }
            class_data_structured = {}
            all_subjects = Subject.objects.all().order_by('name') # Get all subjects for consistent headers

            for item in class_subject_averages:
                class_name = item['student__current_class__name']
                subject_name = item['subject__name']
                avg_score = item['avg_score']
                student_count = item['student_count']

                if class_name not in class_data_structured:
                    class_data_structured[class_name] = {'subjects': {}, 'student_count': 0}
                class_data_structured[class_name]['subjects'][subject_name] = {'avg_score': avg_score, 'student_count': student_count}
                # Update student count for the class (summing up from subjects, but should be consistent)
                # A more robust student count for class should be from Student.objects.filter(current_class__name=class_name).count()
                if class_data_structured[class_name]['student_count'] == 0: # Set only once for the class
                     class_data_structured[class_name]['student_count'] = Student.objects.filter(current_class__name=class_name).count()


            # Prepare data for template
            analysis_data = {
                'overall_subject_averages': list(overall_subject_averages),
                'class_subject_averages_structured': class_data_structured,
                'all_subjects': all_subjects # Pass all subjects for table headers
            }

        context = {
            'form': form,
            'analysis_data': analysis_data,
            'selected_examination': selected_examination,
            'page_heading': 'Whole School Performance Analysis'
        }
        return render(request, self.template_name, context)


class OverallSchoolPerformanceView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'performance/overall_school_performance.html' # New template
    passing_score_threshold = 41 # Define your school's passing score threshold here

    def test_func(self):
        # Ensure only authorized roles can access this view for school-wide stats
        return self.request.user.is_authenticated and self.request.user.role in ['admin', 'headteacher', 'statistic_teacher']

    def get(self, request, *args, **kwargs):
        context = {
            'overall_school_pass_fail': None,
            'per_class_pass_fail': None,
            'page_heading': 'Overall School Performance Dashboard',
            'passing_score_threshold': self.passing_score_threshold # Pass threshold to template
        }

        # Find the most recent academic year and term to analyze by default
        latest_exam = Examination.objects.order_by('-academic_year', '-term', '-date').first()

        if not latest_exam:
            context['message'] = "No examinations found to analyze overall school performance."
            return render(request, self.template_name, context)
        
        # We will analyze based on the latest examination, but aggregate across all relevant classes for the school.
        # If you want to aggregate across *all* exams for the latest year/term, the query would change slightly.
        # For "overall school performance", let's assume it means performance in the latest completed major examination.
        
        # You can add filters here if you want to allow selecting a specific Year or Term for overall analysis
        # For simplicity, we'll use the latest examination found.
        selected_examination_for_overall = latest_exam
        
        # Base queryset for marks for the selected overall examination
        base_marks_queryset = Mark.objects.filter(examination=selected_examination_for_overall)

        # Overall School Passing/Failing Rate for the selected examination
        all_students_in_exam = Student.objects.filter(
            mark__examination=selected_examination_for_overall
        ).distinct()
        total_students_in_exam = all_students_in_exam.count()

        students_with_avg_scores = all_students_in_exam.annotate(
            avg_score_in_exam=Avg('mark__score', filter=Q(mark__examination=selected_examination_for_overall))
        )

        passed_students_count = students_with_avg_scores.filter(
            avg_score_in_exam__gte=self.passing_score_threshold
        ).count()
        
        failed_students_count = total_students_in_exam - passed_students_count
        
        overall_school_pass_fail = {
            'examination_name': selected_examination_for_overall, # Show which exam this data is for
            'total_students': total_students_in_exam,
            'passed_students': passed_students_count,
            'failed_students': failed_students_count,
            'pass_rate': (passed_students_count / total_students_in_exam * 100) if total_students_in_exam > 0 else 0,
            'fail_rate': (failed_students_count / total_students_in_exam * 100) if total_students_in_exam > 0 else 0,
        }
        context['overall_school_pass_fail'] = overall_school_pass_fail


        # Per-Class Passing/Failing Rate for the selected examination
        per_class_pass_fail = []
        classes_in_exam = Class.objects.filter(
            students__mark__examination=selected_examination_for_overall
        ).distinct().order_by('name')

        for cls in classes_in_exam:
            students_in_class_for_exam = all_students_in_exam.filter(current_class=cls)
            total_students_in_class = students_in_class_for_exam.count()

            students_in_class_with_avg_scores = students_in_class_for_exam.annotate(
                avg_score_in_exam=Avg('mark__score', filter=Q(mark__examination=selected_examination_for_overall, mark__student__current_class=cls))
            )
            
            passed_in_class_count = students_in_class_with_avg_scores.filter(
                avg_score_in_exam__gte=self.passing_score_threshold
            ).count()

            failed_in_class_count = total_students_in_class - passed_in_class_count

            per_class_pass_fail.append({
                'class_name': cls.name,
                'total_students': total_students_in_class,
                'passed_students': passed_in_class_count,
                'failed_students': failed_in_class_count,
                'pass_rate': (passed_in_class_count / total_students_in_class * 100) if total_students_in_class > 0 else 0,
                'fail_rate': (failed_in_class_count / total_students_in_class * 100) if total_students_in_class > 0 else 0,
            })
        context['per_class_pass_fail'] = per_class_pass_fail

        return render(request, self.template_name, context)
