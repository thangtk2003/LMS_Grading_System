import os
import json
import subprocess
import re
import math
import mysql.connector
from django.http import JsonResponse

from .helpers import get_dir, prepare_file_paths, write_to_file, cleanup_files
from .c_helpers import handle_c, run_c_tests
from .java_helpers import handle_java, run_java_tests
from .python_helpers import handle_python, run_python_tests
from .sql_helpers import handle_sql, get_mysql_connection , run_sql_test


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
        case 'mysql':
            passed_tests = precheck_sql(language, code, test_cases)

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


def precheck_sql(language, code, test_cases):
    lines = code.splitlines()
    print(lines)
    try:
        # Connect to the MySQL database
        conn = get_mysql_connection()
        cursor = conn.cursor()

        # Set a query timeout (in milliseconds)
        timeout = 3000  # 3000 ms = 3 seconds
        cursor.execute(f"SET SESSION MAX_EXECUTION_TIME = {timeout};")

        # Execute the student's code
        try:
            cursor.execute(lines[0])
            student_result = cursor.fetchall()  # Get the result from the student's query
            print("Student's Result:", student_result)
        except mysql.connector.Error as e:
            return {'error': f"Error executing student's query: {e}"}

        # Execute the expected query
        expected_query = test_cases[0]['query']
        cursor.execute(expected_query)
        expected_result = cursor.fetchall()
        print("Expected Result:", expected_result)

        # Compare student's result with expected result
        if student_result == expected_result:
            print('Pass')
            return {'passed_tests': 1}  # Increment passed tests if the output matches
        else:
            print('Fail')
            return {'passed_tests': 0}  # Return failed test case

    except mysql.connector.Error as e:
        return {'error': f"SQL Error: {e}"}
    
    finally:
        cursor.close()  # Ensure cursor is closed after execution
        conn.close()    # Ensure connection is closed
