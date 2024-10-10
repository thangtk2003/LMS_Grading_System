import json  # To parse JSON data

from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .libs.submission import grade_submission, precheck

from .forms import ExerciseForm, SubmissionForm
from .models import Exercise, Submission

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

def result_detail(request, submission_id):
    submission = Submission.objects.get(id=submission_id)
    return render(request, 'result_detail.html', {'submission': submission})

def result_list(request):
    submissions = Submission.objects.filter(student=request.user)
    return render(request, 'result_list.html', {'submissions': submissions})

def precheck_code(request, exercise_id):
    exercise = get_object_or_404(Exercise, id=exercise_id)
    if request.method == "POST":
        data = json.loads(request.body)
        code = data.get('code')
        language = data.get('language')
        if language == 'python':
            test_cases = exercise.test_cases
        else:
            test_cases = json.loads(exercise.test_cases)        # Assuming test_cases are stored in JSON format  
        result = precheck(code, language, test_cases)
        return JsonResponse({'passed_tests': result['passed_tests'],
                            'hide_test_cases': result['hide_test_cases'],
                            })
    return HttpResponseBadRequest("Invalid request")