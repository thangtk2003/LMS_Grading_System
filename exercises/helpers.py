# import os
# import json
# import subprocess
# import xml.etree.ElementTree as ET
# import re
# import math

# from django.conf import settings
# from django.http import JsonResponse



# def precheck(code, language, test_cases):
#     # Initialize passed test count
#     total_tests = len(test_cases)
#     two_third_tests = math.ceil(total_tests * 2 / 3)
#     precheck_test_cases = test_cases[:two_third_tests]
#     hide_test_cases = math.ceil(total_tests * 1 / 3)
#     passed_tests = 0
    
#     # Define a match-case statement to handle different languages
#     match language:
#         case 'python':       
#             try:
#                 # Save Python code to a temporary file
#                 temp_file = os.path.join(PYTHON_DIR, 'student_code.py')
#                 with open(temp_file, 'w', encoding='utf-8') as f:
#                     f.write(code)

#                 # Extract assert statements
#                 assert_statements = re.findall(r'assert\s+.*', test_cases)
#                 total_tests = len(assert_statements)
#                 two_third_tests = math.ceil(total_tests * 2 / 3)
#                 hide_test_cases = total_tests - two_third_tests
#                 precheck_assertions = assert_statements[:two_third_tests]
                
#                 for idx, assertion in enumerate(precheck_assertions):
#                     def_lines = '\n'.join(test_cases.splitlines()[:2])
#                     test_code = f"""
# import student_code
# {def_lines}
#     {assertion}
# """
#                     test_file = os.path.join(PYTHON_DIR, f'test_case_{idx}.py')
#                     with open(test_file, 'w') as t:
#                         t.write(test_code)                 
                    
#                     # Run the Python code and capture the output
#                     result = subprocess.run(['pytest', test_file, '--tb=short', '--disable-warnings'],
#                                             capture_output=True,
#                                             text=True)
#                     if result.returncode != 0:
#                         return {'error': result.stderr, 'passed_tests': 0, 'hide_test_cases': 0}
#                     output = result.stdout
#                     passed_tests += output.lower().count('passed')
#                     # Delete the test file after use if it exists
#                     if os.path.exists(test_file):
#                         os.remove(test_file)
#                     else:
#                         print(f"File {test_file} does not exist, cannot delete.")
#                 # Delete the Python source code file if it exists
#                 if os.path.exists(temp_file):
#                     os.remove(temp_file)
#             except Exception as e:
#                 output = str(e)
#         case 'text/x-c':
#             try:
#                 # Save C code to a temporary file
#                 temp_file = os.path.join(C_DIR, 'temp_script.c')
#                 with open(temp_file, 'w', encoding='utf-8') as f:
#                     f.write(code)
#                 compiled_executable = os.path.join(C_DIR, 'temp_script.exe')
#                 # Compile C code to an executable file
#                 compile_result = subprocess.run(['gcc', temp_file, '-o', compiled_executable],
#                                                 capture_output=True,
#                                                 text=True)
#                 if compile_result.returncode != 0:
#                     return {'error': compile_result.stderr, 'passed_tests': 0, 'hide_test_cases': 0}
#                 for test in precheck_test_cases:
#                     try:
#                     # Run the executable file and capture the output
#                         result = subprocess.run(compiled_executable, 
#                                                 input=test['input'],
#                                                 capture_output=True, 
#                                                 text=True, 
#                                                 timeout=2
#                                                 )
#                         output = result.stdout.strip()
#                         if output == test['expected_output'].strip():
#                             passed_tests += 1
#                     except subprocess.TimeoutExpired:
#                         print("Timeout")
#                         continue
#                 # Delete the executable file after use
#                 if os.path.exists(compiled_executable):
#                     os.remove(compiled_executable)
#                 else:
#                     print(f"File {compiled_executable} does not exist, cannot delete.")
#                 # Delete the C source code file if it exists
#                 if os.path.exists(temp_file):
#                     os.remove(temp_file)
#             except Exception as e:
#                 output = str(e)
#         case 'text/x-java':
#             try:
#                 # Find the public class name in the Java code
#                 match = re.search(r'public\s+class\s+(\w+)', code)
#                 if match:
#                     class_name = match.group(1)
#                     java_filename = os.path.join(JAVA_DIR, f"{class_name}.java")
#                 else:
#                     output = "No public class found in the Java code."
#                     return JsonResponse({'output': output})

#                 # Save Java code to a file with the same name as the public class
#                 with open(java_filename, 'w', encoding='utf-8') as f:
#                     f.write(code)

#                 # Compile the Java code
#                 compile_result = subprocess.run(['javac', java_filename], 
#                                                 capture_output=True, 
#                                                 text=True)
#                 if compile_result.returncode != 0:
#                     return {'error': compile_result.stderr, 'passed_tests': 0, 'hide_test_cases': 0}
#                 for test in precheck_test_cases:
#                     try:
#                     # Run the executable file and capture the output
#                         result = subprocess.run(['java', '-cp', JAVA_DIR, class_name],
#                                                 input=test['input'], 
#                                                 capture_output=True, 
#                                                 text=True,
#                                                 timeout=2
#                                                 )
#                         output = result.stdout.strip()
#                         if output == test['expected_output'].strip():
#                             passed_tests += 1
#                     except subprocess.TimeoutExpired:
#                         print("Timeout")
#                         continue

#                 # Delete the .class file after use if it exists
#                 class_file = os.path.join(JAVA_DIR, f"{class_name}.class")
#                 if os.path.exists(class_file):
#                     os.remove(class_file)
#                 else:
#                     print(f"File {class_file} does not exist, cannot delete.")

#                 # Delete the Java source code file if it exists
#                 if os.path.exists(java_filename):
#                     os.remove(java_filename)

#             except Exception as e:
#                 output = str(e)

#     return {'passed_tests': passed_tests, 'hide_test_cases': hide_test_cases}