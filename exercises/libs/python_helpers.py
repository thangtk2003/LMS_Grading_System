import os
import subprocess
import xml.etree.ElementTree as ET
from .helpers import write_to_file, parse_test_results, calculate_score, cleanup_files, get_dir, save_xml_result

def generate_test_script(test_file, test_cases):
    test_code = """
import student_code

def run_tests():
    passed_tests = 0
    total_tests = 0
    test_results = []

    # Get all callable functions from student_code
    functions = [getattr(student_code, name) for name in dir(student_code) if callable(getattr(student_code, name))]
"""
    for i, test_case in enumerate(test_cases):
        test_code += f"""
    # Test case {i+1}
    total_tests += 1
    input_data = {test_case['input']}
    expected_output = {test_case['expected_output']}
    result = None
    try:
        # Dynamically split input_data into variables
        # args = []  # List to hold arguments
        # for idx, val in enumerate(input_data):
        #     args.append(val)  # Add each value to the arguments list
        # Loop through the callable functions and run each with input data
        for func in functions:
            func_name = func.__name__
            print(f"Running test case {i+1} on function: {{func_name}}")

            # Dynamically pass arguments to the main() function
            if isinstance(input_data, int) == True:    
                result = func(input_data)  # Unpacking the args list
            else:
                result = func(*input_data)
            if result == expected_output:
                print(f"Test case {i+1} passed")
                test_results.append(('test_{i+1}', 'passed', ''))
                passed_tests += 1
            else:
                print(f"Test case {i+1} failed: Expected {{expected_output}}, Got {{result}}")
                test_results.append(('test_{i+1}', 'failed', f'Expected {{expected_output}}, Got {{result}}'))
    except Exception as e:
        print(f"Test case {i+1} raised an exception: {{str(e)}}")
        test_results.append(('test_{i+1}', 'failed', f'Exception: {{str(e)}}'))
        
"""
    test_code += """
    return test_results, passed_tests, total_tests

if __name__ == "__main__":
    results, passed_tests, total_tests = run_tests()
"""
    write_to_file(test_file, test_code)

    return test_file

def run_test_script(test_file):
    process = subprocess.run(
        ['python', test_file],
        capture_output=True,
        text=True
    )
    return process.stdout

def generate_xml_report(test_results, passed_tests, total_tests):
    root = ET.Element("testsuite", name="PythonTestSuite", tests=str(total_tests), failures=str(total_tests - passed_tests))

    for test in test_results:
        testcase = ET.SubElement(root, "testcase", classname="TestPythonCode", name=test['test_name'])
        if test['result'] == 'failed':
            failure = ET.SubElement(testcase, "failure", message="Test case failed")
            failure.text = test['details']

    result_xml_path = os.path.join(get_dir('python'), 'result.xml')
    tree = ET.ElementTree(root)
    tree.write(result_xml_path)

    return result_xml_path, root

def handle_python(submission, student_code_file, test_file, test_cases):
    # Step 2: Generate the test script to run the cases
    test_file = generate_test_script(test_file, test_cases)
    # Step 3: Run the test script
    output = run_test_script(test_file)
    # Step 4: Parse the test output
    test_results, passed_tests, total_tests = parse_test_results(output, test_cases)
    # Step 5: Generate the XML report
    _, root = generate_xml_report(test_results, passed_tests, total_tests)
    # Step 6: Clean up temporary files
    cleanup_files([student_code_file, test_file])
    score = calculate_score(passed_tests, total_tests)
    return save_xml_result(root, get_dir('python'), "result.xml", score)

def count_passed_tests(output):
    passed_tests = output.lower().count('passed')
    return passed_tests

def run_python_tests(test_file, precheck_test_cases, passed_tests):
    test_file = generate_test_script(test_file, precheck_test_cases)
    # Run the student_code.py script via subprocess
    result = run_test_script(test_file)
    passed_tests = count_passed_tests(result)

    return passed_tests