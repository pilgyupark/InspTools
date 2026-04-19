# 접근 권한 시스템 사용 가이드

## 개요

ParameManager는 사용자 로그인과 접근 권한 기반의 파라미터 제어 시스템을 제공합니다.

## 접근 권한 레벨 체계

```
developer (4) 
    ↓
engineer (3)
    ↓
power_user (2)
    ↓
user (1)
```

높은 레벨의 사용자는 낮은 레벨의 파라미터에 모두 접근 가능합니다.

## 파라미터 접근 제어 설정

### 1. access_level 필드
파라미터가 수정 가능한 최소 권한 레벨을 지정합니다.

```yaml
parameters:
  - name: ransac_threshold
    access_level: developer      # developer 권한 이상만 수정 가능
    # developer, engineer, power_user, user는 read-only
```

### 2. visibility 필드
파라미터 표시 여부를 제어합니다.

```yaml
parameters:
  - name: log_file_path
    access_level: developer
    visibility: hidden           # developer 미만 권한 사용자에게는 완전히 숨김
    # visible (기본값): 권한 없어도 보임 (read-only)
    # hidden: 해당 권한 이상만 볼 수 있음
```

## 사용자 정의 방법

### YAML에 사용자 등록

```yaml
users:
  - username: admin
    password_hash: 8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918
    access_level: developer
    full_name: "관리자"
  
  - username: engineer1
    password_hash: 08f7e3d860b380a991ce0c1af8283c84db99e7eae2d1d65bdc6f38da0b90df8a
    access_level: engineer
    full_name: "엔지니어1"
```

### 비밀번호 해시 생성

Python에서 비밀번호 해시를 생성하려면:

```python
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# 사용 예
password_hash = hash_password("mypassword")
print(password_hash)
```

## 프로그래밍 방식으로 사용자 추가

```python
from ParameManager import User, UserManager, ParameterManager

# 사용자 생성
admin = User.create("admin", "admin123", "developer", "관리자")
engineer = User.create("engineer1", "eng123", "engineer", "엔지니어1")

# 매니저에 추가
manager = ParameterManager()
manager.user_manager.add_user(admin)
manager.user_manager.add_user(engineer)

# 로그인
if manager.user_manager.authenticate("admin", "admin123"):
    current_user = manager.user_manager.current_user
    print(f"로그인 성공: {current_user.full_name} ({current_user.access_level})")
```

## 권한 확인 로직

### 권한 레벨 비교

```python
from ParameManager import AccessLevel

current_level = AccessLevel.ENGINEER
required_level = "developer"

# engineer가 developer 권한의 파라미터에 접근 가능한가?
has_access = current_level.has_access(required_level)  # False
```

### 권한 우선순위

```python
_ACCESS_LEVEL_PRIORITY = {
    "developer": 4,
    "engineer": 3,
    "power_user": 2,
    "user": 1
}
```

## GUI 동작 방식

1. **프로그램 시작**: 로그인 다이얼로그 표시
2. **인증 성공**: 현재 사용자의 권한 레벨에 따라 폼 구성
   - access_level 이상의 파라미터: 수정 가능
   - access_level 미만의 파라미터: read-only (visibility=visible) 또는 숨김 (visibility=hidden)
3. **저장**: 권한이 있는 파라미터만 저장

## 보안 권고사항

1. **비밀번호 해시**: SHA256 사용 (단방향 암호화)
2. **YAML 파일 보안**: 비밀번호 해시가 포함되므로 접근 제한 필요
3. **권한 검증**: 서버/클라이언트 양쪽에서 권한 확인
4. **감사 로그**: 중요 설정 변경 시 로그 기록

## 예제 파일

- `params_example.yaml`: 사용자와 권한이 정의된 예제 설정 파일
- `parameter_manager_example.py`: 로그인 기능이 포함된 실행 파일
