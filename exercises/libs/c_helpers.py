
import xml.etree.ElementTree as ET
import subprocess
from .helpers import save_xml_result, run_test_case, calculate_score, cleanup_files, get_dir


def handle_c(submission, student_code_file, compiled_executable, test_cases, total_tests, passed_tests):
    root = ET.Element("grading_result")

    # Compile C code and check for errors
    if compile_c_code(student_code_file, compiled_executable, root) != 0:
        return save_xml_result(root, get_dir('c'), "result.xml", score=0)

    # Run C program and handle test cases
    for i, test in enumerate(test_cases):
        passed_tests += run_test_case(compiled_executable, test, i, root)

    cleanup_files([compiled_executable, student_code_file])

    score = calculate_score(passed_tests, total_tests)
    return save_xml_result(root, get_dir('c'), "result.xml", score)

def compile_c_code(student_code_file, compiled_executable, root):
    compile_command = ['gcc', student_code_file, '-o', compiled_executable]
    compile_process = subprocess.run(compile_command, capture_output=True, text=True)

    if compile_process.returncode != 0:
        ET.SubElement(root, "error").text = compile_process.stderr

    return compile_process.returncode

def run_c_tests(precheck_test_cases, compiled_executable, passed_tests):
    for test in precheck_test_cases:
        try:
            result = subprocess.run(
                compiled_executable, input=test['input'], 
                capture_output=True, text=True, timeout=2
            )
            if result.stdout.strip() == test['expected_output'].strip():
                passed_tests += 1
        except subprocess.TimeoutExpired:
            print("Timeout")
    return passed_tests