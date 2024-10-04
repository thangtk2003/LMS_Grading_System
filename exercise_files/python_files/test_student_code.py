
import student_code
def test_is_prime_2():
    from student_code import is_prime
    assert is_prime(2) == True  # 2 is prime

def test_is_prime_3():
    from student_code import is_prime
    assert is_prime(3) == True  # 3 is prime

def test_is_prime_4():
    from student_code import is_prime
    assert is_prime(4) == True  # 4 is not prime

def test_is_prime_17():
    from student_code import is_prime
    assert is_prime(17) == True  # 17 is prime

def test_is_prime_20():
    from student_code import is_prime
    assert is_prime(20) == False  # 20 is not prime
