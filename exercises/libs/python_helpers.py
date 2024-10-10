import os
import subprocess
from .helpers import write_to_file, parse_test_results, cleanup_files, get_dir


def handle_python(submission, test_file, student_code_file, test_cases):
    # Write test cases to a test file
    test_code = f"""
import student_code
{test_cases}
"""
    write_to_file(test_file, test_code)

    # Run pytest and capture the result
    result_xml = os.path.join(get_dir('python'), 'result.xml')
    run_pytest(test_file, result_xml)

    # Parse XML for test results
    score = parse_test_results(result_xml)

    cleanup_files([test_file, student_code_file])

    return {'score': score}

def run_pytest(test_file, result_xml):
    subprocess.run(
        ['pytest', test_file, '--tb=short', '--disable-warnings', f'--junitxml={result_xml}'],
        capture_output=True, text=True
    )

def run_python_tests(temp_file, precheck_assertions, passed_tests, def_lines):
    for idx, assertion in enumerate(precheck_assertions):
        test_code = f"""
import student_code
{def_lines}
    {assertion}
"""
        test_file = os.path.join(get_dir('python'), f'test_case_{idx}.py')
        with open(test_file, 'w') as t:
            t.write(test_code)

        result = subprocess.run(
            ['pytest', test_file, '--tb=short', '--disable-warnings'],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return {'error': result.stderr, 'passed_tests': 0}
        passed_tests += result.stdout.lower().count('passed')
        cleanup_files(test_file)
    return passed_tests