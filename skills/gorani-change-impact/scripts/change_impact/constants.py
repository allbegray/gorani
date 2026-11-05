"""change-impact에서 공유하는 상수."""

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".omo",
    ".gorani",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "target",
    "vendor",
    "__pycache__",
}
CATEGORY_RULES = {
    "frontend": [
        "src/app/**/page.*",
        "src/app/**/layout.*",
        "src/pages/**",
        "src/routes/**",
        "app/**/page.*",
        "pages/**",
        "**/*.tsx",
        "**/*.jsx",
        "**/*.vue",
        "**/*.svelte",
    ],
    "api": [
        "openapi/**",
        "**/openapi*.yaml",
        "**/openapi*.yml",
        "**/openapi*.json",
        "**/api/**",
        "**/controllers/**",
        "**/routes/**",
    ],
    "db": [
        "db/migrations/**",
        "migrations/**",
        "**/*.sql",
    ],
    "config": [
        ".env*",
        "docker-compose*.yml",
        "docker-compose*.yaml",
        "compose*.yml",
        "compose*.yaml",
        "k8s/**",
        "helm/**",
        "charts/**",
    ],
    "dependencies": [
        "package.json",
        "**/package-lock.json",
        "**/pnpm-lock.yaml",
        "**/yarn.lock",
        "requirements*.txt",
        "pyproject.toml",
        "uv.lock",
        "poetry.lock",
        "go.mod",
        "go.sum",
        "Cargo.toml",
        "Cargo.lock",
        "pom.xml",
        "build.gradle*",
        "gradle.lockfile",
    ],
    "tests": [
        "tests/**",
        "test/**",
        "**/*.test.*",
        "**/*.spec.*",
        "**/*_test.*",
        "**/test_*.py",
    ],
}
SUGGESTIONS = {
    "frontend": (
        "gorani-site-structure",
        "화면·메뉴·레이아웃 영향 여부를 실제 프론트에서 확인하고 구조도를 갱신합니다.",
    ),
    "api": (
        "gorani-api-contract-diff",
        "이전·새 OpenAPI 스펙을 비교해 breaking change와 클라이언트 영향을 확인합니다.",
    ),
    "db": (
        "gorani-table-spec",
        "테이블 명세를 갱신하고 마이그레이션 잠금·데이터 손실 위험을 확인합니다.",
    ),
    "config": (
        "수동 확인",
        ".env.example·compose·Kubernetes manifest의 환경변수가 서로 일치하는지 확인합니다.",
    ),
    "dependencies": (
        "gorani-cve-scan",
        "의존성 CVE와 라이선스 고지 갱신 필요 여부를 확인합니다. 이어서 gorani-dependency-update를 검토합니다.",
    ),
    "tests": (
        "테스트 실행",
        "변경된 테스트와 영향 범위의 테스트를 실행하고 결과를 기록합니다.",
    ),
}
PRIORITY = ["frontend", "api", "db", "config", "dependencies", "tests"]
