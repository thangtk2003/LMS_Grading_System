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
        #print(f"Error: {err}")
        raise

def execute_sql(language, code, test_cases):
    dict_query_student = split_queries(code)
    if isinstance( dict_query_student,str):
        return dict_query_student
    test_cases = convert_list_to_dict(test_cases)
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
            message_temp += f"<strong>Your Result:</strong>" + "&nbsp;&nbsp;&nbsp;&nbsp;" +str(student_result.get('result')) + "<br>"
            

            # Execute the expected query
            expected_query = test_cases.get(query_key)
            if expected_query:
                cursor.execute(expected_query)
                expected_result = cursor.fetchall()
                message_temp += f"<strong>Expected Result:</strong>" + "&nbsp;&nbsp;&nbsp;&nbsp;" +str(expected_result) + "<br>"

                if student_result.get('result', []) == expected_result:
                    passed_tests += 1
                    #print(f'{query_key}: Pass')
                    # Thêm nội dung vào thẻ alert success khi pass
                    message.append(
                        f'<div class="alert alert-success" role="alert">'
                        f'{message_temp}<div style="text-align: center;"><strong>&lt;&lt;&lt;&lt;&lt;&lt; Pass &gt;&gt;&gt;&gt;&gt;&gt;</strong></div>'
                        f'</div>'
                    )
                else:
                    error_msg = student_result.get('error',"Please check the expected Result !!!")
                    #print(f'{query_key}: Fail - Error: {error_msg}')
                    # Thêm nội dung vào thẻ alert danger khi fail
                    message.append(
                        f'<div class="alert alert-danger" role="alert">'
                        f'{message_temp} <div style="text-align: center;"><strong>{error_msg}</strong><br><strong>&lt;&lt;&lt;&lt;&lt;&lt; Fail &gt;&gt;&gt;&gt;&gt;&gt;</strong></div>'
                        f'</div>'
                    )
            header_msg = f"""
            <div style="text-align: center;">
            <h5> <span style="color: black;"> &lt;&lt;&lt;&lt;&lt;&lt;RUNNING TEST CASES&gt;&gt;&gt;&gt;&gt;&gt;</span></h5>
            <h6> <span style="color: red;">You have passed {passed_tests} out of 
            {len(test_cases)} total test cases. </span></h6></div><br>
            
            """
        message.insert(0, header_msg)
    except mysql.connector.Error as e:
        return {'error': f"SQL Error: {e}"}
    
    finally:
        if cursor is not None:  # Check if cursor was created
            cursor.close()  # Ensure cursor is closed after execution
        if conn is not None:  # Check if connection was created
            conn.close() 
    combined_message = ''.join(message)
    #print(combined_message)
    return combined_message

def split_queries(queries: str) -> dict:
    # Regular expression to match 'query_' followed by the number and capture the query
    pattern = r'(query_\d+):\s*(.+?)(?=(query_\d+:)|$)'
    
    # Find all matches using the regular expression
    matches = re.findall(pattern, queries, re.DOTALL)
    if not matches:
        return """<div class="alert alert-warning" role="alert">
    No queries found in the input string. <br> 
    Queries should start with <strong>query_1</strong>, <strong>query_2</strong>, etc.
</div>"""
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
        return {'result': student_result}
    except ProgrammingError as e:
        #print(f"Programming Error executing student's query: {e}")
        return {'error': f"Programming Error: {e}"}
    except DataError as e:
        #print(f"Data Error executing student's query: {e}")
        return {'error': f"Data Error: {e}"}
    except IntegrityError as e:
        #print(f"Integrity Error executing student's query: {e}")
        return {'error': f"Integrity Error: {e}"}
    except OperationalError as e:
        #print(f"Operational Error executing student's query: {e}")
        return {'error': f"Operational Error: {e}"}
    except Error as e:
        #print(f"General SQL Error executing student's query: {e}")
        return {'error': f"General SQL Error: {e}"}
    except Exception as e:
        # This will catch any other type of exception that is not caught by the specific mysql.connector errors
        #print(f"Unexpected error: {e}")
        return {'error': f"Unexpected Error: {e}"}