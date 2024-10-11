import os
import subprocess
import xml.etree.ElementTree as ET
import re

from django.conf import settings


# Directory where the code and test files will be saved
# EXERCISE_DIR = os.path.normpath(os.path.join(settings.BASE_DIR, 'exercise_files'))
# os.makedirs(EXERCISE_DIR, exist_ok=True)

# PYTHON_DIR = os.path.normpath(os.path.join(EXERCISE_DIR, 'python_files'))
# os.makedirs(PYTHON_DIR, exist_ok=True)

# C_DIR = os.path.normpath(os.path.join(EXERCISE_DIR, 'c_files'))
# os.makedirs(C_DIR, exist_ok=True)

# JAVA_DIR = os.path.normpath(os.path.join(EXERCISE_DIR, 'java_files'))
# os.makedirs(JAVA_DIR, exist_ok=True)

def get_dir(language):
    EXERCISE_DIR = os.path.normpath(os.path.join(settings.BASE_DIR, 'exercise_files'))
    os.makedirs(EXERCISE_DIR, exist_ok=True)
    if language == 'python':
        return os.path.normpath(os.path.join(EXERCISE_DIR, 'python_files'))
    elif language == 'c':
        return os.path.normpath(os.path.join(EXERCISE_DIR, 'c_files'))
    elif language == 'java':
        return os.path.normpath(os.path.join(EXERCISE_DIR, 'java_files'))
    else:
        raise ValueError(f"Unsupported language: {language}")

def prepare_file_paths(language, student_code):
    if language == 'python':
        student_code_file = os.path.join(get_dir(language), 'student_code.py')
        test_file = os.path.join(get_dir(language), 'test_student_code.py')
        return student_code_file, test_file, None, None
    elif language == 'c':
        student_code_file = os.path.join(get_dir(language), 'student_code.c')
        compiled_executable = os.path.join(get_dir(language), 'student_program.exe')
        return student_code_file, None, compiled_executable, None
    elif language == 'java':
        match = re.search(r'public\s+class\s+(\w+)', student_code)
        if match:
            class_name = match.group(1)
            student_code_file = os.path.join(get_dir(language), f"{class_name}.java")
            return student_code_file, None, None, class_name
        else:
            return None, None, None, None

def write_to_file(file_path, content):
    with open(file_path, 'w') as f:
        f.write(content)

def run_test_case(executable, test, test_index, root):
    test_case_element = ET.SubElement(root, "test_case", id=str(test_index+1))
    ET.SubElement(test_case_element, "input").text = test['input']
    ET.SubElement(test_case_element, "expected_output").text = test['expected_output']

    try:
        run_process = subprocess.run(executable.split(), input=test['input'], text=True, capture_output=True, timeout=2)
        output = run_process.stdout.strip()
        ET.SubElement(test_case_element, "actual_output").text = output

        if output == test['expected_output'].strip():
            ET.SubElement(test_case_element, "result").text = "passed"
            return 1
        else:
            ET.SubElement(test_case_element, "result").text = "failed"
    except subprocess.TimeoutExpired:
        ET.SubElement(test_case_element, "result").text = "timeout"

    return 0

def parse_test_results(output, test_cases):
    passed_tests = output.lower().count('passed')
    total_tests = len(test_cases)
    
    # Split the output into lines
    output_lines = output.splitlines()
    
    test_results = []
    for i, test_case in enumerate(test_cases):
        # Ensure we don't go out of bounds
        if i < len(output_lines):
            test_result = output_lines[i]  # Get the i-th test result line
        else:
            # If there are not enough lines, append an error or a default
            test_result = "failed: No result available for this test case"
        
        # Default result is 'passed'
        result = {'test_name': f"test_{i+1}", 'result': 'passed'}
        
        # Update result based on the test output
        if 'failed' in test_result.lower():
            result['result'] = 'failed'
            if 'failed:' in test_result:
                result['details'] = test_result.split("failed:")[1].strip()
            else:
                result['details'] = "Unknown failure."
        elif 'exception' in test_result.lower():
            result['result'] = 'failed'
            if 'raised an exception:' in test_result:
                result['details'] = test_result.split("raised an exception:")[1].strip()
            else:
                result['details'] = "Exception occurred but no details provided."
        
        test_results.append(result)

    return test_results, passed_tests, total_tests

def calculate_score(passed_tests, total_tests):
    return (passed_tests / total_tests) * 100 if total_tests > 0 else 100

def save_xml_result(root, dir_path, file_name, score):
    ET.SubElement(root, "score").text = str(score)
    tree = ET.ElementTree(root)
    xml_file_path = os.path.join(dir_path, file_name)
    tree.write(xml_file_path)
    return {'score': score}

def cleanup_files(file_paths):
    for file_path in file_paths:
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            print(f"File {file_path} does not exist, cannot delete.")
