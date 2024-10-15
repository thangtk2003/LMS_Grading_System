import mysql.connector
import xml.etree.ElementTree as ET
from .helpers import save_xml_result, calculate_score, get_dir


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

def handle_sql(submission, test_cases, total_tests, passed_tests):
    root = ET.Element("grading_result")

    # Connect to MySQL database
    conn = get_mysql_connection()
    cursor = conn.cursor()

    for i, test in enumerate(test_cases):
        passed_tests += run_sql_test(cursor, test, i, root)

    cursor.close()
    conn.close()

    score = calculate_score(passed_tests, total_tests)
    return save_xml_result(root, get_dir('sql'), "result.xml", score)

def run_sql_test(cursor, test, test_index, root):
    try:
        cursor.execute(test['query'])
        result = cursor.fetchall()

        if result == test['expected_output']:
            return 1
        else:
            error_element = ET.SubElement(root, "test_case", id=str(test_index))
            error_element.text = f"Expected {test['expected_output']}, but got {result}"
    except mysql.connector.Error as e:
        error_element = ET.SubElement(root, "test_case", id=str(test_index))
        error_element.text = f"SQL Error: {e}"

    return 0
