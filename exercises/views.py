from django.shortcuts import render, redirect,  get_object_or_404
from .models import Exercise, Submission
from .forms import SubmissionForm, ExerciseForm
from django.contrib import messages
from django.conf import settings
import os  # To create temporary directories
import pytest  # To run test cases
import tempfile  # To create temporary files
import json  # To parse test cases
import subprocess  # To run student code

# Create your views here.

def exercise_list(request):
    exercises = Exercise.objects.all()
    return render(request, 'exercise_list.html', {'exercises': exercises})

def exercise_add(request):
    if request.method == 'POST':
        form = ExerciseForm(request.POST)
        if form.is_valid():
            form.save()  # Save the exercise to the database
            return redirect('exercise_list')  # Redirect to a page that shows all exercises
    else:
        form = ExerciseForm()

    return render(request, 'exercise_add.html', {'form': form})

def exercise_detail(request, exercise_id):
    exercise = Exercise.objects.get(id=exercise_id)
    form = SubmissionForm()
    return render(request, 'exercise_form.html', {'exercise': exercise, 'form': form})

def submit_code(request, exercise_id):
    exercise = get_object_or_404(Exercise, id=exercise_id)
    if request.method == "POST":
        form = SubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.student = request.user
            submission.exercise = exercise
            submission.save()
            result = grade_submission(submission)
            submission.score = result['score']
            submission.save()
            return redirect('result_detail', submission_id=submission.id)
        else:
            print(form.errors)  # Print form errors to debug
            print(request.POST)  # Print form data for debugging
    return redirect('exercise_list')

# Directory where the code and test files will be saved
EXERCISE_DIR = os.path.normpath(os.path.join(settings.BASE_DIR, 'exercise_files'))
os.makedirs(EXERCISE_DIR, exist_ok=True)

def grade_submission(submission):
    # Get student's code
    student_code = submission.code

    # Get the test cases (Python test code) for the exercise
    test_cases = submission.exercise.test_cases

    # Define file paths for student code and test cases
    student_code_file = os.path.join(EXERCISE_DIR, 'student_code.py')
    test_file = os.path.join(EXERCISE_DIR, 'test_student_code.py')

    # Write student's code to a file
    with open(student_code_file, 'w') as f:
        f.write(student_code)

    # Write test cases to a separate file
    test_code = f"""
import student_code
{test_cases}
"""
    with open(test_file, 'w') as f:
        f.write(test_code)

    # Run pytest and capture the exit code
    result = pytest.main([test_file, '--tb=short', '--disable-warnings'])

    # Determine the score based on the exit code
    if result == pytest.ExitCode.OK:
        score = 100  # All tests passed
    elif result == pytest.ExitCode.TESTS_FAILED:
        score = 0  # Some or all tests failed
    else:
        score = 0  # Handle other cases like usage error or interruption

    return {'score': score}

def result_detail(request, submission_id):
    submission = Submission.objects.get(id=submission_id)
    return render(request, 'result_detail.html', {'submission': submission})

def result_list(request):
    submissions = Submission.objects.filter(student=request.user)
    return render(request, 'result_list.html', {'submissions': submissions})
