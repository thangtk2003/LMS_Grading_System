import os
import json
import subprocess
import re
import math

from django.http import JsonResponse

from .helpers import get_dir, prepare_file_paths, write_to_file, cleanup_files
from .c_helpers import handle_c, run_c_tests
from .java_helpers import handle_java, run_java_tests
from .python_helpers import handle_python, run_python_tests

def grade_submission(submission):
    # Get student's code and language
    student_code = submission.code
    language = submission.exercise.language # 'python', 'java', or 'c'
    
    # Load test cases for Python or parse JSON for Java/C
    test_cases = json.loads(submission.exercise.test_cases)
    total_tests = len(test_cases)
    passed_tests = 0

    # Define file paths based on the language
    student_code_file, test_file, compiled_executable, class_name = prepare_file_paths(language, student_code)
    
    if not student_code_file:
        return JsonResponse({'output': "No public class found in the Java code."})

    # Write student code to a file
    write_to_file(student_code_file, student_code)

    match language:
        case 'python':
            return handle_python(submission, student_code_file, test_file, test_cases)
        case 'c':
            return handle_c(submission, student_code_file, compiled_executable, test_cases, total_tests, passed_tests)
        case 'java':
            return handle_java(submission, student_code_file, class_name, test_cases, total_tests, passed_tests)

    return {'score': 0}

def precheck(code, language, test_cases):
    total_tests = len(test_cases)
    two_third_tests = math.ceil(total_tests * 2 / 3)
    precheck_test_cases = test_cases[:two_third_tests]
    hide_test_cases = total_tests - two_third_tests
    passed_tests = 0

    match language:
        case 'python':
            passed_tests = precheck_python(language, code, precheck_test_cases, passed_tests, hide_test_cases)
        case 'c':
            passed_tests = precheck_c(language, code, precheck_test_cases, passed_tests, hide_test_cases)
        case 'java':
            passed_tests = precheck_java(language, code, precheck_test_cases, passed_tests, hide_test_cases)

    return {'passed_tests': passed_tests, 'hide_test_cases': hide_test_cases}

def precheck_python(language, code, precheck_test_cases, passed_tests, hide_test_cases):
    try:
        temp_file = os.path.join(get_dir(language), 'student_code.py')
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(code)
        test_file = os.path.join(get_dir(language), 'test_script.py')
        passed_tests = run_python_tests(test_file, precheck_test_cases, passed_tests)
        cleanup_files([temp_file, test_file])
    except Exception as e:
        return {'error': str(e), 'passed_tests': passed_tests, 'hide_test_cases': hide_test_cases}
    
    return passed_tests

def precheck_c(language, code, precheck_test_cases, passed_tests, hide_test_cases):
    try:
        temp_file = os.path.join(get_dir(language), 'temp_script.c')
        compiled_executable = os.path.join(get_dir(language), 'temp_script.exe')

        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(code)

        compile_result = subprocess.run(
            ['gcc', temp_file, '-o', compiled_executable],
            capture_output=True, text=True
        )
        if compile_result.returncode != 0:
            return {'error': compile_result.stderr, 'passed_tests': 0, 'hide_test_cases': 0}

        passed_tests = run_c_tests(precheck_test_cases, compiled_executable, passed_tests)
        cleanup_files([compiled_executable, temp_file])

    except Exception as e:
        return {'error': str(e), 'passed_tests': passed_tests, 'hide_test_cases': hide_test_cases}
    
    return passed_tests

def precheck_java(language, code, precheck_test_cases, passed_tests, hide_test_cases):
    try:
        match = re.search(r'public\s+class\s+(\w+)', code)
        if not match:
            return {'error': "No public class found in the Java code.", 'passed_tests': 0, 'hide_test_cases': 0}

        class_name = match.group(1)
        java_filename = os.path.join(get_dir(language), f"{class_name}.java")

        with open(java_filename, 'w', encoding='utf-8') as f:
            f.write(code)

        compile_result = subprocess.run(
            ['javac', java_filename],
            capture_output=True, text=True
        )
        if compile_result.returncode != 0:
            return {'error': compile_result.stderr, 'passed_tests': 0, 'hide_test_cases': 0}

        passed_tests = run_java_tests(class_name, precheck_test_cases, passed_tests)
        cleanup_files([java_filename, os.path.join(get_dir(language), f"{class_name}.class")])

    except Exception as e:
        return {'error': str(e), 'passed_tests': passed_tests, 'hide_test_cases': hide_test_cases}
    
    return passed_tests