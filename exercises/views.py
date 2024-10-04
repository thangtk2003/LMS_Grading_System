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
import xml.etree.ElementTree as ET

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

PYTHON_DIR = os.path.normpath(os.path.join(EXERCISE_DIR, 'python_files'))
os.makedirs(PYTHON_DIR, exist_ok=True)

C_DIR = os.path.normpath(os.path.join(EXERCISE_DIR, 'c_files'))
os.makedirs(C_DIR, exist_ok=True)

JAVA_DIR = os.path.normpath(os.path.join(EXERCISE_DIR, 'java_files'))
os.makedirs(JAVA_DIR, exist_ok=True)


def grade_submission(submission):
    # Get student's code and language
    student_code = submission.code
    language = submission.exercise.language # Language will be 'python', 'java', or 'c'

    # Get the test cases for the exercise
    if language == 'python':
        test_cases = submission.exercise.test_cases
    else:
        test_cases = json.loads(submission.exercise.test_cases)
    
    passed_tests = 0
    total_tests = len(test_cases)

    # Prepare file paths for student code
    if language == 'python':
        student_code_file = os.path.join(PYTHON_DIR, 'student_code.py')
        test_file = os.path.join(PYTHON_DIR, 'test_student_code.py')
    elif language == 'c':
        student_code_file = os.path.join(C_DIR, 'student_code.c')
        compiled_executable = os.path.join(C_DIR, 'student_program')
    elif language == 'java':
        student_code_file = os.path.join(JAVA_DIR, 'StudentCode.java')
        
    # Write student's code to a file
    with open(student_code_file, 'w') as f:
        f.write(student_code)

    # Define a match-case statement to handle different languages
    match language:
        case 'python':
            # Write test cases to a separate file
            test_code = f"""
        import student_code
        {test_cases}
        """
            with open(test_file, 'w') as f:
                f.write(test_code)

            # Run pytest using subprocess and save the result to an XML file
            result_xml = os.path.join(PYTHON_DIR, 'result.xml')
            process = subprocess.run(
                ['pytest', test_file, '--tb=short', '--disable-warnings', f'--junitxml={result_xml}'],
                capture_output=True,
                text=True
            )
            # Parse the XML to get test results
            tree = ET.parse(result_xml)
            root = tree.getroot()

            # Get information from testsuite
            total_tests = 0
            total_failures = 0

            for testsuite in root.findall('testsuite'):
                total_tests += int(testsuite.get('tests', 0))
                total_failures += int(testsuite.get('failures', 0))

            if total_tests > 0:
                score = (1 - total_failures / total_tests) * 100
            else:
                score = 100  # Default score if no tests were run
        case 'c':
            compile_command = ['gcc', student_code_file, '-o', compiled_executable]
            
            # Compile the C code using GCC
            compile_process = subprocess.run(
                compile_command,
                capture_output=True,
                text=True
            )
            # Create an XML root element
            root = ET.Element("grading_result")
            # Check if compilation succeeded
            if compile_process.returncode != 0:
                # If compilation fails, return a score of 0 with an error message
                error_element = ET.SubElement(root, "error")
                error_element.text = compile_process.stderr
                
                # Save the XML result with the compilation error
                tree = ET.ElementTree(root)
                xml_file_path = os.path.join(C_DIR, "result.xml")
                tree.write(xml_file_path)

                return {'score': 0, 'error': compile_process.stderr}
            
            # Now run the compiled program with the test cases
            test_results = ET.SubElement(root, "test_cases")

            # Now run the compiled program with the test cases
            for i, test in enumerate(test_cases):
                test_case_element = ET.SubElement(test_results, "test_case", id=str(i+1))
                input_element = ET.SubElement(test_case_element, "input")
                input_element.text = test['input']
                
                expected_output_element = ET.SubElement(test_case_element, "expected_output")
                expected_output_element.text = test['expected_output']

                try:
                    # Run the compiled C program with test case input
                    run_process = subprocess.run(compiled_executable, 
                                                input=test['input'], 
                                                text=True, 
                                                capture_output=True, 
                                                timeout=2
                                                )
                    output = run_process.stdout.strip()
                    actual_output_element = ET.SubElement(test_case_element, "actual_output")
                    actual_output_element.text = output

                    # Compare output with expected output
                    if output == test['expected_output'].strip():
                        passed_tests += 1
                        result_element = ET.SubElement(test_case_element, "result")
                        result_element.text = "passed"
                    else:
                        result_element = ET.SubElement(test_case_element, "result")
                        result_element.text = "failed"

                except subprocess.TimeoutExpired:
                    # If the program takes too long, consider the test as failed
                    result_element = ET.SubElement(test_case_element, "result")
                    result_element.text = "timeout"
                    continue

            # Calculate the score as the percentage of passed tests
            if total_tests > 0:
                score = (passed_tests / total_tests) * 100
            else:
                score = 100  # Default score if no tests were run
            # Add score to XML
            score_element = ET.SubElement(root, "score")
            score_element.text = str(score)
            
            # Save the XML file with the results
            tree = ET.ElementTree(root)
            xml_file_path = os.path.join(C_DIR, "result.xml")
            tree.write(xml_file_path)
        case 'java':
            compile_command = ['javac', student_code_file]
            
            # Compile the Java code using javac
            compile_process = subprocess.run(
                compile_command,
                capture_output=True,
                text=True
            )
            # Create an XML root element
            root = ET.Element("grading_result")
            # Check if compilation succeeded
            if compile_process.returncode != 0:
                # If compilation fails, return a score of 0 with an error message
                error_element = ET.SubElement(root, "error")
                error_element.text = compile_process.stderr
                
                # Save the XML result with the compilation error
                tree = ET.ElementTree(root)
                xml_file_path = os.path.join(JAVA_DIR, "result.xml")
                tree.write(xml_file_path)

                return {'score': 0, 'error': compile_process.stderr}
            
            # Now run the compiled program with the test cases
            test_results = ET.SubElement(root, "test_cases")

            # Now run the compiled program with the test cases
            for i, test in enumerate(test_cases):
                test_case_element = ET.SubElement(test_results, "test_case", id=str(i+1))
                input_element = ET.SubElement(test_case_element, "input")
                input_element.text = test['input']
                
                expected_output_element = ET.SubElement(test_case_element, "expected_output")
                expected_output_element.text = test['expected_output']

                try:
                    # Run the compiled C program with test case input
                    run_process = subprocess.run(
                                                ['java', '-cp', JAVA_DIR, 'StudentCode'], 
                                                input=test['input'], 
                                                text=True, 
                                                capture_output=True, 
                                                timeout=2
                                                )
                    output = run_process.stdout.strip()
                    actual_output_element = ET.SubElement(test_case_element, "actual_output")
                    actual_output_element.text = output

                    # Compare output with expected output
                    if output == test['expected_output'].strip():
                        passed_tests += 1
                        result_element = ET.SubElement(test_case_element, "result")
                        result_element.text = "passed"
                    else:
                        result_element = ET.SubElement(test_case_element, "result")
                        result_element.text = "failed"

                except subprocess.TimeoutExpired:
                    # If the program takes too long, consider the test as failed
                    result_element = ET.SubElement(test_case_element, "result")
                    result_element.text = "timeout"
                    continue

            # Calculate the score as the percentage of passed tests
            if total_tests > 0:
                score = (passed_tests / total_tests) * 100
            else:
                score = 100  # Default score if no tests were run
            # Add score to XML
            score_element = ET.SubElement(root, "score")
            score_element.text = str(score)
            
            # Save the XML file with the results
            tree = ET.ElementTree(root)
            xml_file_path = os.path.join(JAVA_DIR, "result.xml")
            tree.write(xml_file_path)

    return {'score': score}

# def grade_submission(submission):
    # Directory where the C code and test files will be saved
    # C_DIR = os.path.normpath(os.path.join(EXERCISE_DIR, 'c_files'))
    # os.makedirs(C_DIR, exist_ok=True)
    # # Get student's C code
    # student_code = submission.code

    # # Get the test cases for the exercise (assuming input and expected output)
    # test_cases = json.loads(submission.exercise.test_cases)  # List of test cases with 'input' and 'expected_output'

    # passed_tests = 0
    # total_tests = len(test_cases)
    # # Define file paths for student C code and compiled executable
    # student_code_file = os.path.join(C_DIR, 'student_code.c')

    # # Write student's C code to a file
    # with open(student_code_file, 'w') as f:
    #     f.write(student_code)

    # compiled_executable = os.path.join(C_DIR, 'student_program')
    # compile_command = ['gcc', student_code_file, '-o', compiled_executable]
    
    # # Compile the C code using GCC
    # compile_process = subprocess.run(
    #     compile_command,
    #     capture_output=True,
    #     text=True
    # )
    # # Create an XML root element
    # root = ET.Element("grading_result")
    # # Check if compilation succeeded
    # if compile_process.returncode != 0:
    #     # If compilation fails, return a score of 0 with an error message
    #     error_element = ET.SubElement(root, "error")
    #     error_element.text = compile_process.stderr
        
    #     # Save the XML result with the compilation error
    #     tree = ET.ElementTree(root)
    #     xml_file_path = os.path.join(C_DIR, "result.xml")
    #     tree.write(xml_file_path)

    #     return {'score': 0, 'error': compile_process.stderr}
    
    # # Now run the compiled program with the test cases
    # test_results = ET.SubElement(root, "test_cases")

    # # Now run the compiled program with the test cases
    # for i, test in enumerate(test_cases):
    #     test_case_element = ET.SubElement(test_results, "test_case", id=str(i+1))
    #     input_element = ET.SubElement(test_case_element, "input")
    #     input_element.text = test['input']
        
    #     expected_output_element = ET.SubElement(test_case_element, "expected_output")
    #     expected_output_element.text = test['expected_output']

    #     try:
    #         # Run the compiled C program with test case input
    #         run_process = subprocess.run(compiled_executable, 
    #                                     input=test['input'], 
    #                                     text=True, 
    #                                     capture_output=True, 
    #                                     timeout=2
    #                                     )
    #         output = run_process.stdout.strip()
    #         actual_output_element = ET.SubElement(test_case_element, "actual_output")
    #         actual_output_element.text = output

    #         # Compare output with expected output
    #         if output == test['expected_output'].strip():
    #             passed_tests += 1
    #             result_element = ET.SubElement(test_case_element, "result")
    #             result_element.text = "passed"
    #         else:
    #             result_element = ET.SubElement(test_case_element, "result")
    #             result_element.text = "failed"

    #     except subprocess.TimeoutExpired:
    #         # If the program takes too long, consider the test as failed
    #         result_element = ET.SubElement(test_case_element, "result")
    #         result_element.text = "timeout"
    #         continue

    # # Calculate the score as the percentage of passed tests
    # if total_tests > 0:
    #     score = (passed_tests / total_tests) * 100
    # else:
    #     score = 100  # Default score if no tests were run
    # # Add score to XML
    # score_element = ET.SubElement(root, "score")
    # score_element.text = str(score)
    
    # # Save the XML file with the results
    # tree = ET.ElementTree(root)
    # xml_file_path = os.path.join(C_DIR, "result.xml")
    # tree.write(xml_file_path)

    # return {'score': score}

# def grade_submission(submission):
    # # Directory where the JAVA code and test files will be saved
    # JAVA_DIR = os.path.normpath(os.path.join(EXERCISE_DIR, 'java_files'))
    # os.makedirs(JAVA_DIR, exist_ok=True)
    # # Get student's Java code
    # student_code = submission.code

    # # Get the test cases for the exercise (assuming input and expected output)
    # test_cases = json.loads(submission.exercise.test_cases)  # List of test cases with 'input' and 'expected_output'

    # passed_tests = 0
    # total_tests = len(test_cases)
    # # Define file paths for student Java code and compiled executable
    # student_code_file = os.path.join(JAVA_DIR, 'StudentCode.java')

    # # Write student's Java code to a file
    # with open(student_code_file, 'w') as f:
    #     f.write(student_code)

    #compiled_executable = os.path.join(JAVA_DIR, 'StudentCode')
    # compile_command = ['javac', student_code_file]
    
    # # Compile the Java code using javac
    # compile_process = subprocess.run(
    #     compile_command,
    #     capture_output=True,
    #     text=True
    # )
    # # Create an XML root element
    # root = ET.Element("grading_result")
    # # Check if compilation succeeded
    # if compile_process.returncode != 0:
    #     # If compilation fails, return a score of 0 with an error message
    #     error_element = ET.SubElement(root, "error")
    #     error_element.text = compile_process.stderr
        
    #     # Save the XML result with the compilation error
    #     tree = ET.ElementTree(root)
    #     xml_file_path = os.path.join(JAVA_DIR, "result.xml")
    #     tree.write(xml_file_path)

    #     return {'score': 0, 'error': compile_process.stderr}
    
    # # Now run the compiled program with the test cases
    # test_results = ET.SubElement(root, "test_cases")

    # # Now run the compiled program with the test cases
    # for i, test in enumerate(test_cases):
    #     test_case_element = ET.SubElement(test_results, "test_case", id=str(i+1))
    #     input_element = ET.SubElement(test_case_element, "input")
    #     input_element.text = test['input']
        
    #     expected_output_element = ET.SubElement(test_case_element, "expected_output")
    #     expected_output_element.text = test['expected_output']

    #     try:
    #         # Run the compiled C program with test case input
    #         run_process = subprocess.run(
    #                                     ['java', '-cp', JAVA_DIR, 'StudentCode'], 
    #                                     input=test['input'], 
    #                                     text=True, 
    #                                     capture_output=True, 
    #                                     timeout=2
    #                                     )
    #         output = run_process.stdout.strip()
    #         actual_output_element = ET.SubElement(test_case_element, "actual_output")
    #         actual_output_element.text = output

    #         # Compare output with expected output
    #         if output == test['expected_output'].strip():
    #             passed_tests += 1
    #             result_element = ET.SubElement(test_case_element, "result")
    #             result_element.text = "passed"
    #         else:
    #             result_element = ET.SubElement(test_case_element, "result")
    #             result_element.text = "failed"

    #     except subprocess.TimeoutExpired:
    #         # If the program takes too long, consider the test as failed
    #         result_element = ET.SubElement(test_case_element, "result")
    #         result_element.text = "timeout"
    #         continue

    # # Calculate the score as the percentage of passed tests
    # if total_tests > 0:
    #     score = (passed_tests / total_tests) * 100
    # else:
    #     score = 100  # Default score if no tests were run
    # # Add score to XML
    # score_element = ET.SubElement(root, "score")
    # score_element.text = str(score)
    
    # # Save the XML file with the results
    # tree = ET.ElementTree(root)
    # xml_file_path = os.path.join(JAVA_DIR, "result.xml")
    # tree.write(xml_file_path)

    # return {'score': score}

def result_detail(request, submission_id):
    submission = Submission.objects.get(id=submission_id)
    return render(request, 'result_detail.html', {'submission': submission})

def result_list(request):
    submissions = Submission.objects.filter(student=request.user)
    return render(request, 'result_list.html', {'submissions': submissions})
