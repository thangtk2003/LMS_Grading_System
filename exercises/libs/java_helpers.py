import xml.etree.ElementTree as ET
import subprocess
import os
from .helpers import save_xml_result, run_test_case, calculate_score, cleanup_files, get_dir

def handle_java(submission, student_code_file, class_name, test_cases, total_tests, passed_tests):
    root = ET.Element("grading_result")
    
    # Compile Java code and check for errors
    if compile_java_code(student_code_file, root) != 0:
        return save_xml_result(root, get_dir('java'), "result.xml", score=0)

    # Run Java program and handle test cases
    for i, test in enumerate(test_cases):
        passed_tests += run_test_case(f"java -cp {get_dir('java')} {class_name}", test, i, root)

    cleanup_files([student_code_file, os.path.join(get_dir('java'), f"{class_name}.class")])

    score = calculate_score(passed_tests, total_tests)
    return save_xml_result(root, get_dir('java'), "result.xml", score)

def compile_java_code(student_code_file, root):
    compile_process = subprocess.run(['javac', student_code_file], capture_output=True, text=True)

    if compile_process.returncode != 0:
        ET.SubElement(root, "error").text = compile_process.stderr

    return compile_process.returncode

def run_java_tests(class_name, precheck_test_cases, passed_tests):
    for test in precheck_test_cases:
        try:
            result = subprocess.run(
                ['java', '-cp', get_dir('java'), class_name],
                input=test['input'], capture_output=True, text=True, timeout=2
            )
            if result.stdout.strip() == test['expected_output'].strip():
                passed_tests += 1
        except subprocess.TimeoutExpired:
            print("Timeout")
    return passed_tests