# Operato Runner CI/CD 가이드

이 디렉토리는 Operato Runner의 CI/CD 관련 파일을 포함합니다.

## 배포 방법

### 사전 요구사항

- Kubernetes 클러스터
- Helm 3.x
- kubectl 설정

### Helm 차트 배포

1. 값 설정:

```bash
# values.yaml 파일을 필요에 맞게 수정
cp values.yaml my-values.yaml
```

2. 배포:

```bash
# 배포
helm install operato-runner ./operato-runner -f my-values.yaml

# 업그레이드
helm upgrade operato-runner ./operato-runner -f my-values.yaml
```

3. 상태 확인:

```bash
kubectl get pods -l app.kubernetes.io/name=operato-runner
```

### 환경별 배포

각 환경별 values 파일을 생성하여 관리할 수 있습니다:

- `values-dev.yaml`: 개발 환경
- `values-staging.yaml`: 스테이징 환경
- `values-prod.yaml`: 프로덕션 환경

```bash
# 개발 환경 배포
helm install operato-runner-dev ./operato-runner -f values-dev.yaml

# 스테이징 환경 배포
helm install operato-runner-staging ./operato-runner -f values-staging.yaml

# 프로덕션 환경 배포
helm install operato-runner-prod ./operato-runner -f values-prod.yaml
```

## CI/CD 파이프라인 통합

이 프로젝트는 다음과 같은 CI/CD 파이프라인과 통합할 수 있습니다:

- GitHub Actions
- GitLab CI
- Jenkins

예제 구성 파일은 추후 이 디렉토리에 추가될 예정입니다.
