import mysql.connector
import xml.etree.ElementTree as ET
from .helpers import save_xml_result, calculate_score, get_dir
import re
from mysql.connector import Error, ProgrammingError, OperationalError, DataError, IntegrityError

def get_mysql_connection():
    """
    Establish a connection to the MySQL database.
    Returns the connection object if successful, otherwise raises an exception.
    """
    db_config = {
        'host': '103.174.213.139',
        'port': 3323,
        'user': 'coderbyte',
        'password': 'HBjTcb1y7!5rq',
        'database': 'coderbyte_db',
        'charset': 'utf8mb4'
    }

    try:
        conn = mysql.connector.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
            charset=db_config['charset']
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        raise

def execute_sql(language, code, test_cases):
    dict_query_student = split_queries(code)
    test_cases = convert_list_to_dict(test_cases)
    print(dict_query_student)
    print(test_cases)
    message = []
    passed_tests = 0
    try:
        # Connect to the MySQL database
        conn = get_mysql_connection()
        cursor = conn.cursor()
        # Loop through each query in the student's dict_query_student
        for query_key in dict_query_student:
            # Execute the student's code
            message_temp = ""
            student_result = execute_student_query(cursor, dict_query_student.get(query_key))  # Get the result from the student's query
            message_temp += f"Student's Result for {query_key}:" + str(student_result) + "<br>"
            

            # Execute the expected query
            expected_query = test_cases.get(query_key)
            cursor.execute(expected_query)
            expected_result = cursor.fetchall()
            message_temp += f"Expected Result for {query_key}:" + str(expected_result) + "<br>"

            # Compare student's result with expected result
            if student_result.get('result', []) == expected_result:
                passed_tests += 1
                print(f'{query_key}: Pass')
                message.append(message_temp + f'{query_key}: Pass' + "<br>") 
            else:
                error_msg = student_result.get('error', [])
                print(f'{query_key}: Fail - Error: {error_msg}')
                message.append(message_temp + f'{query_key}: Fail - Error: {error_msg}' + "<br>")
        header_msg = f"""
        RUNNING TEST CASES: <br>
        {passed_tests} TEST CASES PASSED ON {len(test_cases)} TOTAL TEST CASES <br>
        """
        message.insert(0, header_msg)
    except mysql.connector.Error as e:
        return {'error': f"SQL Error: {e}"}
    
    finally:
        cursor.close()  # Ensure cursor is closed after execution
        conn.close()    # Ensure connection is closed
    
    return message

def split_queries(queries: str) -> dict:
    # Regular expression to match 'query_' followed by the number and capture the query
    pattern = r'(query_\d+):\s*(.+?)(?=(query_\d+:)|$)'
    
    # Find all matches using the regular expression
    matches = re.findall(pattern, queries, re.DOTALL)
    
    # Create a dictionary from the matches, replacing newlines with spaces
    query_dict = {match[0]: match[1].replace('\n', '').strip() for match in matches}
    
    return query_dict

def convert_list_to_dict(query_list):
    # Initialize an empty dictionary to hold the combined result
    query_dict = {}
    
    # Iterate through the list of dictionaries
    for query in query_list:
        # Update the dictionary with each query's key-value pair
        query_dict.update(query)
    
    return query_dict

def execute_student_query(cursor, query):
    """
    Executes a student's SQL query and handles possible errors.

    Args:
        cursor: The MySQL cursor object used to execute the query.
        query (str): The SQL query to be executed.

    Returns:
        dict: A dictionary with the result of the query or an error message.
    """
    try:
        cursor.execute(query)  # Execute the provided query
        student_result = cursor.fetchall()  # Get the result from the student's query
        print("Student's Result:", student_result)
        return {'result': student_result}
    except ProgrammingError as e:
        print(f"Programming Error executing student's query: {e}")
        return {'error': f"Programming Error: {e}"}
    except DataError as e:
        print(f"Data Error executing student's query: {e}")
        return {'error': f"Data Error: {e}"}
    except IntegrityError as e:
        print(f"Integrity Error executing student's query: {e}")
        return {'error': f"Integrity Error: {e}"}
    except OperationalError as e:
        print(f"Operational Error executing student's query: {e}")
        return {'error': f"Operational Error: {e}"}
    except Error as e:
        print(f"General SQL Error executing student's query: {e}")
        return {'error': f"General SQL Error: {e}"}
    except Exception as e:
        # This will catch any other type of exception that is not caught by the specific mysql.connector errors
        print(f"Unexpected error: {e}")
        return {'error': f"Unexpected Error: {e}"}