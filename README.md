# InspTools
이미지 검사 도구

## 파라미터 관리 (ParameManager)

`ParameManager.py`는 YAML 기반의 계층적 파라미터 관리 시스템입니다. 모듈 > 기능 > 그룹 > 파라미터의 4단계 계층 구조를 지원합니다.

### 주요 기능

- **계층적 구조**: 모듈(Module) > 기능(Feature) > 그룹(Group) > 파라미터(Parameter)
- **고유 파라미터 식별**: 같은 이름의 파라미터를 다른 계층(모듈/기능/그룹)에서 사용 가능
- **자동 GUI 생성**: Tkinter 기반 폼 자동 생성 (탭 인터페이스)
- **다양한 파라미터 타입**: string, int, float, bool, choice, path 등
- **파일 경로 선택**: path 타입 파라미터에 파일 다이얼로그 자동 생성
- **접근 권한 관리**: 사용자 로그인 및 접근 레벨별 파라미터 제어
- **YAML 저장/로드**: 파라미터 정의, 값, 사용자 정보를 YAML로 관리

### 접근 권한 레벨 (Access Level)

| 레벨 | 설명 |
|------|------|
| developer | 개발자 (최상 권한) |
| engineer | 엔지니어 |
| power_user | 파워 사용자 |
| user | 일반 사용자 (최하 권한) |

권한이 높을수록 더 많은 파라미터에 접근 가능합니다. 권한이 없는 파라미터는:
- **read-only**: 값을 볼 수만 있고 수정 불가
- **hidden**: 완전히 감춰짐 (visibility: hidden 설정 시)

### YAML 구조 예제

```yaml
users:
  - username: admin
    password_hash: 8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918
    access_level: developer
    full_name: "관리자"

parameters:
  # 같은 이름의 파라미터를 다른 계층에서 사용 가능
  - name: threshold
    label: "임계값 (이미지 처리)"
    type: float
    value: 0.5
    module: "이미지 처리"
    feature: "전처리"
    group: "필터"
    access_level: user
    
  - name: threshold
    label: "임계값 (특징점 매칭)"
    type: float
    value: 5.0
    module: "특징점 매칭"
    feature: "알고리즘"
    group: "정확도"
    access_level: engineer
    
  # 고유 ID는 자동으로 생성: 모듈:기능:그룹:이름
  # "이미지 처리:전처리:필터:threshold"
  # "특징점 매칭:알고리즘:정확도:threshold"

values:
  # 값은 고유 ID로 저장되거나 파라미터 이름으로 접근 가능
```

### 프로그래밍 방식으로 파라미터 접근

```python
from ParameManager import ParameterManager

manager = ParameterManager.load_yaml("params_example.yaml")

# 방법 1: 이름으로 접근 (같은 이름이 여러 개면 첫 번째 반환)
value1 = manager.get("threshold")

# 방법 2: 계층 구조로 접근 (정확한 파라미터)
value2 = manager.get_by_hierarchy(
    module="이미지 처리",
    feature="전처리",
    group="필터",
    name="threshold"
)

# 방법 3: 고유 ID로 접근
unique_id = "이미지 처리:전처리:필터:threshold"
value3 = manager.values.get(unique_id)

# 설정 (권한 체크 포함)
manager.set_by_hierarchy(
    module="특징점 매칭",
    feature="알고리즘",
    group="정확도",
    name="threshold",
    value=7.5
)
```

### 테스트 계정

- **ID**: admin, **PW**: admin, **권한**: developer
- **ID**: engineer1, **PW**: engineer, **권한**: engineer
- **ID**: user1, **PW**: user, **권한**: user

### 예제 실행

```bash
python parameter_manager_example.py
```

### 파일 구조

- `params_example.yaml`: 4단계 계층 파라미터 정의 예제
- `parameter_manager_example.py`: GUI 예제 실행 파일
