# reports/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Avg, Q, F, Sum
from students.models import Student, Class, Examination, Mark
from users.models import CustomUser
from .utils import role_required
from django.db.models import Count
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML, CSS
from io import BytesIO
import os
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import ExaminationSelectionForm

def get_grade(avg):
    if avg >= 81:
        return "A"
    elif avg >= 61:
        return "B"
    elif avg >= 41:
        return "C"
    elif avg >= 21:
        return "D"
    else:
        return "F"

def select_exam_for_report(request):
    if request.method == 'POST':
        form = ExaminationSelectionForm(request.POST)
        if form.is_valid():
            examination_id = form.cleaned_data['examination'].id
            # Redirect to the main report view with the selected exam ID
            return redirect('reports:overall_report_with_attempt_status', examination_id=examination_id)
    else:
        form = ExaminationSelectionForm()
    
    return render(request, 'reports/select_exam.html', {'form': form})

def overall_report_with_attempt_status(request, examination_id):
    classes = Class.objects.all().order_by('name')
    report_data = []

    for cls in classes:
        total_students = Student.objects.filter(current_class=cls).count()

        # Count distinct students who have a Mark entry for this exam,
        # where the score is greater than 0.
        attempted_students_count = Mark.objects.filter(
            student__current_class=cls,
            examination_id=examination_id,
            score__gt=0  # <-- CORRECTED: Use 'score' instead of 'mark'
        ).values('student').distinct().count()

        not_attempted_students_count = total_students - attempted_students_count

        report_data.append({
            'class_name': cls.name,
            'total_students': total_students,
            'attempted_count': attempted_students_count,
            'not_attempted_count': not_attempted_students_count,
            'class_id': cls.id,
            'examination_id': examination_id,
        })
    
    context = {
        'report_data': report_data,
    }
    return render(request, 'reports/overall_exam_report.html', context)

@role_required(['headteacher', 'academic_teacher', 'statistic_teacher', 'class_teacher'])
def class_performance_summary(request):
    """Class performance summary for all teachers."""
    classes = Class.objects.annotate(
        total_students=Count('students', distinct=True),
        students_with_marks=Count(
            'students',
            filter=Q(students__mark__score__isnull=False),
            distinct=True
        ),
        graduated_students=Count(
            'students',
            filter=Q(students__status='graduated'),
            distinct=True
        )
    ).annotate(
        not_attempted=F('total_students') - F('students_with_marks')
    )
    return render(request, 'reports/class_performance_summary.html', {'classes': classes})

@role_required(['headteacher', 'admin'])
def teachers_registered(request):
    """List of registered teachers."""
    teachers = CustomUser.objects.filter(role='teacher')
    return render(request, 'reports/teachers_registered.html', {'teachers': teachers})

@role_required(['headteacher', 'academic_teacher', 'statistic_teacher', 'admin'])
def graduated_students(request):
    year = request.GET.get('year')
    students = None

    if year:
        students = Student.objects.filter(status='Graduated', graduation_year=year)

    years = Student.objects.filter(status='Graduated') \
                           .values_list('graduation_year', flat=True) \
                           .distinct().order_by('-graduation_year')

    return render(request, 'reports/graduated_students.html', {
        'students': students,
        'years': years,
        'selected_year': year
    })

def get_student_performance_data(class_obj, examination_obj):
    """
    Efficiently gets and processes student performance data for a specific class and exam.
    """
    student_scores_queryset = (
        Mark.objects.filter(
            student__current_class=class_obj,
            examination=examination_obj, # CRITICAL FIX: Filter by examination
            score__isnull=False
        )
        .values('student')
        .annotate(
            total_score=Sum('score'),
            average=Avg('score')
        )
        .order_by('-total_score')
    )
    
    students_with_position = []
    
    # Efficiently get student objects in a single query
    student_ids = [s['student'] for s in student_scores_queryset]
    students_map = {
        s.id: s for s in Student.objects.filter(id__in=student_ids)
    }

    # Assign position and grade while handling ties
    previous_score = None
    current_position = 1
    for i, s in enumerate(student_scores_queryset):
        # Handle ties: if the score is the same as the previous one, use the same position
        if s['total_score'] != previous_score:
            current_position = i + 1
        previous_score = s['total_score']
        
        avg = s['average']
        
        students_with_position.append({
            'student': students_map.get(s['student']), # Use the pre-fetched student object
            'total_score': s['total_score'],
            'average': avg,
            'grade': get_grade(avg),
            'position': current_position
        })

    return students_with_position

@role_required(['headteacher', 'academic_teacher', 'statistic_teacher', 'class_teacher'])
def top_and_bottom_students(request, class_id, examination_id):
    """View for displaying Top and Bottom Students"""
    class_obj = get_object_or_404(Class, pk=class_id)
    examination_obj = get_object_or_404(Examination, pk=examination_id)
    
    students_data = get_student_performance_data(class_obj, examination_obj)
    
    top_students_data = students_data[:10]
    bottom_students_data = students_data[-10:]
    
    return render(request, 'reports/top_bottom_students.html', {
        'class_name': class_obj.name,
        'class_obj': class_obj,
        'examination_id': examination_obj.id,   # Important for URLs
        'top_students': top_students_data,
        'bottom_students': bottom_students_data,
    })

@role_required(['headteacher', 'academic_teacher', 'statistic_teacher', 'admin'])
def select_class_for_report(request, report_type):
    """Shows a list of classes for selection."""
    classes = Class.objects.all().order_by('name')
    context = {
        'classes': classes,
        'report_type': report_type.replace('_', ' ').title(),
        'page_title': 'Select a Class to View Report',
    }
    return render(request, 'reports/select_class_for_report.html', context)

@role_required(['headteacher', 'academic_teacher', 'statistic_teacher', 'admin'])
def choose_exam(request):
    exams = Examination.objects.all().order_by('-date')
    return render(request, 'reports/choose_exam.html', {'exams': exams})

def select_exam_for_not_attempted(request):
    """
    Renders a form to select an examination for the 'Not Attempted' report.
    """
    if request.method == 'POST':
        form = ExaminationSelectionForm(request.POST)
        if form.is_valid():
            examination_id = form.cleaned_data['examination'].id
            # Redirect to the overall report view
            return redirect('reports:overall_report_with_attempt_status', examination_id=examination_id)
    else:
        form = ExaminationSelectionForm()
    
    return render(request, 'reports/select_exam.html', {'form': form})

@role_required(['headteacher', 'academic_teacher', 'statistic_teacher', 'admin'])
def not_attempted_students(request, class_id, examination_id):
    # Get the class object to be used in the template
    current_class = get_object_or_404(Class, pk=class_id)
    
    # Get all students in the class
    all_students_in_class = Student.objects.filter(current_class=current_class)

    # Get the IDs of students who attempted the exam (mark > 0)
    # This query finds the IDs of students who have a Mark entry for this exam.
    attempted_student_ids = Mark.objects.filter(
        student__current_class=current_class,
        examination_id=examination_id,
        score__gt=0  # Use your corrected field name
    ).values_list('student_id', flat=True)

    # Exclude students who are in the attempted_student_ids list
    not_attempted_students = all_students_in_class.exclude(
        id__in=attempted_student_ids
    ).order_by('first_name', 'last_name')

    context = {
        'students': not_attempted_students,
        'current_class': current_class,
        'examination_id': examination_id,
    }
    return render(request, 'reports/not_attempted_students.html', context)

@role_required(['headteacher', 'academic_teacher', 'statistic_teacher', 'admin'])
def students_not_attempted_exam(request, class_id, examination_id):
    class_obj = get_object_or_404(Class, pk=class_id)
    examination = get_object_or_404(Examination, pk=examination_id)

    # Get a list of student IDs who have at least one mark for this specific exam in this class.
    students_with_marks_ids = Mark.objects.filter(
        student__current_class=class_obj,
        examination=examination
    ).values_list('student__id', flat=True).distinct()
    
    # Now, find all active students in the class and exclude the ones who have a mark.
    not_attempted = Student.objects.filter(
        current_class=class_obj,
        status='active'
    ).exclude(
        id__in=students_with_marks_ids
    ).order_by('first_name')
    
    return render(request, 'reports/not_attempted_students.html', {
        'class_name': class_obj.name,
        'students': not_attempted,
        'examination': examination,
    })

@login_required
def select_class_for_report(request, report_type):
    """
    Renders a page for a user to select a class for a specific report type.
    """
    if request.user.role not in ['headteacher', 'academic_teacher', 'statistic_teacher']:
        messages.error(request, "You are not authorized to view this page.")
        return redirect('teacher_dashboard')

    classes = Class.objects.all()
    context = {
        'classes': classes,
        'report_type': report_type # Pass the received report type to the template
    }
    return render(request, 'reports/select_class_for_report.html', context)

def select_exam_for_top_bottom(request):
    """
    Handles the selection of an examination for the Top and Bottom Students report.
    """
    if request.method == 'POST':
        form = ExaminationSelectionForm(request.POST)
        if form.is_valid():
            examination_id = form.cleaned_data['examination'].id
            # Redirect to the next view with the selected exam ID
            return redirect('reports:select_class_for_top_bottom', examination_id=examination_id)
    else:
        # For a GET request, initialize a new, empty form
        form = ExaminationSelectionForm()
    
    return render(request, 'reports/select_exam_for_top_bottom.html', {'form': form})

@role_required(['headteacher', 'academic_teacher', 'statistic_teacher', 'admin'])
def select_class_for_top_bottom(request, examination_id):
    """Shows a list of classes for selection for a specific exam."""
    classes = Class.objects.all().order_by('name')
    context = {
        'classes': classes,
        'examination_id': examination_id,
        'page_title': 'Select a Class to View Top/Bottom Students',
    }
    return render(request, 'reports/select_class_for_top_bottom.html', context)

def get_student_performance_data(class_obj, examination_obj):
    """Helper function to get and process student performance data."""
    # Filter marks by both class and examination
    student_scores = (
        Mark.objects.filter(
            student__current_class=class_obj,
            examination=examination_obj,
            score__isnull=False
        )
        .values('student')
        .annotate(
            total_score=Sum('score'),
            average=Avg('score')
        )
        .order_by('-total_score')
    )
    
    students_with_position = []
    position = 1
    for s in student_scores:
        student_obj = Student.objects.get(pk=s['student'])
        avg = s['average']
        
        students_with_position.append({
            'student': student_obj,
            'total_score': s['total_score'],
            'average': avg,
            'grade': get_grade(avg),
            'position': position
        })
        position += 1
    return students_with_position

@role_required(['headteacher', 'academic_teacher', 'statistic_teacher', 'class_teacher'])
def top_and_bottom_students(request, class_id, examination_id):
    """Generates a web view of the top and bottom students report."""
    class_obj = get_object_or_404(Class, pk=class_id)
    examination_obj = get_object_or_404(Examination, pk=examination_id)
    
    students_data = get_student_performance_data(class_obj, examination_obj)
    
    top_students_data = students_data[:10]
    bottom_students_data = students_data[-10:]
    
    return render(request, 'reports/top_bottom_students.html', {
        'class_name': class_obj.name,
        'examination_name': examination_obj.name, # Pass examination name to template
        'class_obj': class_obj,
        'top_students': top_students_data,
        'bottom_students': bottom_students_data,
    })

def top_bottom_pdf(request, class_id, examination_id):
    """
    Generates a PDF report for the top and bottom students.
    """
    # NOTE: You must first query the data, just as in your top_and_bottom_students view.
    # For now, let's assume you have the context variables ready.
    context = {
        'class_name': 'Standard 6', # Placeholder data
        'top_students': [],          # Placeholder data
        'bottom_students': [],       # Placeholder data
        'examination_name': 'First Term Examination', # Placeholder
    }

    # Render the HTML template with the context
    html_string = render_to_string('reports/top_bottom_students.html', context)

    # Path to your static CSS file for PDF styling (optional but recommended)
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'css', 'pdf_styles.css')

    # Convert HTML to PDF
    pdf_file = HTML(string=html_string).write_pdf(
        stylesheets=[CSS(css_path)] if os.path.exists(css_path) else []
    )

    # Return the PDF as a Django HttpResponse
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'filename="top_bottom_report.pdf"'
    return response

@role_required(['headteacher', 'academic_teacher', 'statistic_teacher'])
def student_performance_trend(request, student_id):
    student = get_object_or_404(Student, pk=student_id)

    # Use the Mark model instead of ExaminationResult
    performance_data = Mark.objects.filter(
        student=student
    ).values(
        'examination__name'
    ).annotate(
        average_score=Avg('score')
    ).order_by('examination__date')

    context = {
        'student': student,
        'performance_data': list(performance_data)
    }
    return render(request, 'reports/student_performance_trend.html', context)

@role_required(['headteacher', 'academic_teacher', 'statistic_teacher'])
def class_comparison(request, examination_id):
    examination = get_object_or_404(Examination, pk=examination_id)

    # Use the Mark model instead of ExaminationResult
    class_averages = Mark.objects.filter(
        examination=examination
    ).values(
        'student__current_class__name'
    ).annotate(
        class_average=Avg('score')
    ).order_by('student__current_class__name')

    context = {
        'examination': examination,
        'class_averages': list(class_averages)
    }
    return render(request, 'reports/class_comparison.html', context)

def select_comparison_exam(request):
    examinations = Examination.objects.all().order_by('-date')
    return render(request, 'reports/select_comparison_exam.html', {'examinations': examinations})

def handle_comparison_selection(request):
    exam_id = request.GET.get('exam_id')
    if not exam_id:
        return redirect('reports:select_comparison_exam')
    return redirect('reports:class_comparison', examination_id=exam_id)
