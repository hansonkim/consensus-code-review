"""샘플 코드 - 리뷰 데모용

이 코드에는 의도적으로 여러 문제점이 포함되어 있습니다.
"""


def vulnerable_function(user_input):
    """SQL Injection 취약점이 있는 함수"""
    # CRITICAL: SQL Injection 취약점
    query = f"SELECT * FROM users WHERE username='{user_input}'"
    return query


def inefficient_algorithm(numbers):
    """성능 문제가 있는 알고리즘"""
    # MAJOR: O(n²) 알고리즘 - 최적화 필요
    result = []
    for i in range(len(numbers)):
        for j in range(len(numbers)):
            if i != j:
                result.append((numbers[i], numbers[j]))
    return result


def poor_error_handling(filename):
    """에러 처리가 부족한 함수"""
    # MAJOR: 에러 처리 누락
    file = open(filename, 'r')
    content = file.read()
    file.close()
    return content


def bad_naming(x, y):
    """가독성이 낮은 코드"""
    # MINOR: 의미 없는 변수명
    z = x + y
    w = z * 2
    return w


def duplicate_code_example():
    """중복 코드 예시"""
    # MINOR: 중복 코드
    user_list = []
    for i in range(10):
        user_list.append(f"user{i}")

    admin_list = []
    for i in range(5):
        admin_list.append(f"admin{i}")

    return user_list, admin_list


# SUGGESTION: Type hints 추가 권장
def missing_type_hints(name, age, email):
    """Type hints가 없는 함수"""
    return {
        "name": name,
        "age": age,
        "email": email
    }


if __name__ == "__main__":
    # 테스트 실행
    print(vulnerable_function("admin"))
    print(inefficient_algorithm([1, 2, 3]))
    print(bad_naming(5, 10))
