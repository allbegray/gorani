---
name: gorani-dependency-update
description: 현재 언어·프레임워크 라인의 최신 안정 버전으로 정렬할지, CVE가 있는 패키지만 재정의할지, 라인까지 넘어 최신 안정으로 올릴지 사용자와 정한 뒤 저장소의 네이티브 도구로 의존성을 갱신한다. 의존성 업데이트, 취약 패키지 교체, 프레임워크 호환 버전 유지가 필요할 때 사용.
---

# 의존성 업데이트

언어와 패키지 매니저가 달라도 같은 결정 순서를 따릅니다. 먼저 현재 언어·프레임워크 **라인**(예: Java 21, Spring Boot 4.1.x, Next.js 14.x)을 정하고, 그 라인 안에서 최신 안정 버전으로 정렬할지, CVE만 재정의할지, 라인까지 넘을지 사용자와 정합니다. 그 생태계의 네이티브 도구로 적용하고, 별도 스크립트로 모든 생태계를 감싸지 않습니다.

## 전제

- 저장소의 언어, 패키지 매니저, lockfile, 프레임워크, 빌드·테스트 명령을 먼저 확인합니다.
- 사용자가 모드를 고르지 않았으면 모드 1을 기본으로 하고, 기본값을 사용했다고 보고합니다.
- 한 번에 하나의 생태계와 하나의 워크스페이스를 다룹니다. 모노레포 루트에서 전체를 한꺼번에 올리지 않습니다.
- 레지스트리와 audit 도구를 사용할 수 있어야 후보 버전과 CVE를 확인할 수 있습니다. 네트워크가 없으면 확인하지 못한 부분을 명시하고 추측하지 않습니다.
- "최신 안정 버전"은 레지스트리의 stable/dist-tag latest를 뜻합니다. canary, next, beta, RC는 사용자가 명시하지 않으면 제외합니다.
- 적용 전에 계획을 보여 주고, 모드 3·major 변경·프레임워크 관리 밖 재정의는 명시적으로 확인받습니다.
- 사용자 지시 없이 커밋·푸시·PR을 만들지 않습니다.

## 모드 선택

사용자에게 아래 세 가지를 제시합니다. 선택이 없으면 1번을 씁니다.

| 모드 | 이름 | 동작 | manifest 범위 |
| --- | --- | --- | --- |
| 1 | 언어·프레임워크 최신 안정화 기준 (기본) | 현재 언어·프레임워크 라인 안의 최신 안정 패치로 프레임워크와 관리 의존성을 정렬하고, 비관리 직접 의존성은 같은 major/line 안에서 갱신 | 프레임워크 패치·BOM과 같은 major 내 의존성 버전은 변경. `^`·`~` 범위 표기는 유지 |
| 2 | 1 + CVE 재정의 | 모드 1 이후에도 남은 취약점만 최소 수정 버전으로 재정의 | CVE 패키지만 예외적으로 변경 |
| 3 | 전체 최신 안정 버전 | 언어·프레임워크 라인까지 넘어 모든 직접 의존성을 최신 안정 버전으로 올림 | 전체 변경 |

- "라인"은 지금 프로젝트가 선언한 언어·프레임워크의 major/minor 흐름입니다. 예: Java 21, Spring Boot 4.1.x, Spring Cloud 2025.1.x, Next.js 14.x, React 18.x(peer 범위), Angular 17.x.
- 모드 1은 그 라인의 **최신 안정 패치**로 정렬합니다. Boot 4.1.1→4.1.2, Cloud 2025.1.3→2025.1.4, Next 14.2.5→14.2.35처럼 같은 라인 안에서 움직입니다.
- 모드 1은 라인을 넘지 않습니다. Boot 4.1.x→4.2.x/5.x, Next 14.x→15.x/16.x, React 18.x→19.x, Angular 17.x→18.x는 모드 3 또는 별도 결정입니다.
- 모드 1의 목적은 "현재 버전 고정"이 아니라 **현재 라인의 최신 안정화**입니다. 현재 라인의 최신 패치가 이미 설치돼 있으면 그때만 유지합니다.
- 모드 2는 모드 1의 결과를 기준으로 하고, CVE를 고치기 위해 필요한 최소 버전만 재정의합니다. 라인 업그레이드가 필요하면 예외로 기록하고 확인받습니다.
- 모드 3은 프레임워크와 그 패키지 패밀리, 비관리 의존성의 major까지 함께 올립니다. peer 충돌과 빌드 실패를 각오해야 하므로 확인 없이 진행하지 않습니다.
- 사용자가 "그냥 최신으로"라고 하면 모드 3으로 해석하되, 프레임워크 라인까지 바뀐다는 점을 먼저 알립니다.
- 사용자가 "보안만"이라고 하면 모드 2로 해석합니다.

모드별 장단점:

| 모드 | 장점 | 주의 |
| --- | --- | --- |
| 1 | 현재 언어·프레임워크 라인의 호환성을 지키고 변경 범위가 작음 | 일부 CVE가 남을 수 있음. 프레임워크 패치를 빠르게 따라가는 패스트 팔로워 운영이 필요 |
| 2 | 모드 1의 잔여 CVE까지 보완 | BOM property override·버전 불일치로 의존성 관리가 지저분해질 수 있음. override 제거 계획을 함께 세워야 함 |
| 3 | 모든 직접 의존성을 최신 안정으로 맞춤 | 호환성이 깨질 수 있음. 호환성 체크와 충분한 테스트 케이스가 필수이고, major 변경은 분리하는 것이 권장됨 |

선택 기준:

- 호환성이 최우선이고 릴리스 일정이 촉박하면 모드 1. 대신 프레임워크 패치·EOL을 빠르게 따라가는 패스트 팔로워 전략을 함께 정합니다.
- CVE 대응 SLA가 있거나 보안 수정이 필요하면 모드 2. override가 만든 BOM 이탈을 추적하고, 이후 패치에 흡수할 계획을 적습니다.
- 프레임워크 라인을 현대화하거나 major 업그레이드를 계획하고 테스트 여력이 있으면 모드 3. 호환성 체크와 회귀 테스트를 전제로 합니다.

사용자에게는 짧게 이렇게 묻습니다. "의존성 업데이트 방식을 선택해 주세요. 1) 현재 언어·프레임워크 라인의 최신 안정화(기본, 호환성 우선·패스트 팔로워) 2) 1 + CVE 수정 버전 재정의(보안 보완·관리 복잡도 증가) 3) 라인까지 넘는 전체 최신 안정 버전(호환성·테스트 필수)"

## 절차

1. 저장소를 파악합니다. 언어 런타임 버전, 프레임워크 라인(예: Spring Boot 4.1.x, Next.js 14.x), 패키지 매니저, lockfile, 워크스페이스 구성, 빌드·테스트·린트 명령을 확인합니다.
2. 모드를 확정합니다. 사용자가 고르지 않았으면 모드 1을 쓰고 그 사실을 보고합니다.
3. 직접 의존성 인벤토리를 만듭니다. 현재 버전, 현재 라인 안의 최신 안정 후보, 라인 밖 최신 안정 버전, production/dev 구분, 직접/전이 구분을 적습니다.
4. 프레임워크 관리 의존성을 판정합니다. 프레임워크의 선언 파일, BOM, SDK manifest, peerDependencies, 공식 업데이트 도구 중 무엇이 근거인지 확인하고 기록합니다.
5. 모드별 목표 버전을 정합니다. 현재 라인 안 최신화, CVE 수정, 라인 밖 최신 안정 중 무엇인지 패키지마다 표시합니다.
6. 계획을 표로 보여 줍니다. major 변경, 프레임워크 관리 밖 재정의, CVE 수정, peer 충돌 가능성을 별도로 표시합니다.
7. 확인받은 범위만 적용합니다. lockfile을 손으로 고치지 않고, 해당 생태계의 업데이트·설치 명령을 사용합니다.
8. 검증합니다. 설치 상태, lockfile diff, 빌드, 테스트, 린트, 타입 검사, 프레임워크 진단 명령을 실행합니다.
9. CVE 모드였다면 audit를 다시 실행해 수정 버전이 반영됐는지 확인합니다.
10. 결과를 보고합니다. 바뀐 패키지, 유지한 패키지와 이유, 수정한 CVE, 검증 결과, 롤백 방법을 적습니다.

## 프레임워크 관리 판정

프레임워크가 관리한다는 것은 "같은 이름의 패키지 패밀리"라는 뜻이 아니라, 프레임워크의 선언이나 도구가 해당 의존성의 호환 버전을 결정한다는 뜻입니다. 근거를 찾지 못하면 관리 대상으로 단정하지 말고, 관리하지 않는 것으로 두되 가정을 기록합니다.

| 생태계 | 예 | 관리 근거 | 확인 방법 |
| --- | --- | --- | --- |
| Node | Next.js | `next`의 peerDependencies, React/ReactDOM 호환 범위 | `node -p "require('next/package.json').peerDependencies"` |
| Node | Expo | `expo`의 `bundledNativeModules.json`, `expo install` | `npx expo install --check` |
| Node | Angular | `@angular/*` 패밀리, `rxjs`, `zone.js`, `typescript` | `ng version`, `ng update` |
| Node | Nuxt | `nuxt`가 기본 구성하는 `vue`, `vue-router` | `nuxt info`, 패키지 선언 |
| Node | SvelteKit·Remix·React Native·NestJS | peerDependencies 또는 패키지 패밀리 | 해당 패키지의 package.json과 공식 업데이트 명령 |
| Java | Spring Boot | parent/BOM의 dependencyManagement, 버전을 생략한 선언 | `mvn help:effective-pom`, `mvn dependency:tree` |
| Java | Quarkus·Micronaut | BOM이 관리하는 버전 | `mvn dependency:tree`, `gradle dependencies` |
| .NET | Central Package Management | `Directory.Packages.props`, 프레임워크 참조 | `dotnet list package` |
| Python | constraints·lock | `constraints.txt`, `-c`, Poetry/uv lock | `pip check`, `poetry show`, `uv lock --check` |
| Flutter | SDK 고정 패키지 | `sdk: flutter`, `pubspec.lock`의 `source: sdk` | `flutter pub outdated`, `flutter pub deps` |
| Ruby | Rails 계열 | Gemfile과 lockfile, `bundle update rails`가 함께 갱신하는 패밀리 | `bundle outdated` |
| PHP | Symfony·Laravel | composer 제약과 프레임워크 패키지 | `composer outdated --direct` |
| Rust | workspace 상속 | `workspace = true`, `Cargo.lock` | `cargo tree` |
| Go | module | 정확한 버전 고정, 범위 없음 | `go list -m -u all` |

- Spring Boot는 `tomcat.version`, `jackson-bom.version`, `jackson-2-bom.version` 같은 BOM property로 특정 버전만 재정의할 수 있습니다. 이 경우 BOM 이탈로 기록하고, 가능하면 이후 Boot 패치로 흡수할 계획을 함께 적습니다.

- 프레임워크 본체도 관리 대상으로 봅니다. 모드 1에서는 현재 라인의 **최신 안정 패치**까지 올립니다. 라인 자체를 넘는 업그레이드는 모드 3 또는 별도 결정입니다.
- 모드 1의 최신 라인 패치로 해결되는 CVE는 그 패치에 포함합니다. 최신 라인 패치로도 해결되지 않으면 모드 2 재정의 또는 라인 업그레이드 결정으로 보고합니다.
- 프레임워크 패밀리는 함께 움직여야 합니다. Angular, Expo, Spring Boot BOM, Flutter SDK처럼 도구가 일괄 갱신하는 경우 개별 패키지만 올리지 않습니다.
- 판정 근거는 계획 표에 적습니다. 예: "next 14.2.5의 peerDependencies가 react ^18.2.0을 선언".

## 모드별 판정

### 모드 1 — 언어·프레임워크 최신 안정화 기준

- 먼저 기준 라인을 기록합니다. 언어 런타임(예: Java 21), 프레임워크 라인(예: Spring Boot 4.1.x, Spring Cloud 2025.1.x, Next.js 14.x), peer 범위(예: React 18.x), SDK 라인(예: Flutter 3.x)을 적습니다.
- 프레임워크 본체는 현재 라인의 최신 안정 패치/마이너로 올립니다. 예: Spring Boot 4.1.1→4.1.2, Spring Cloud 2025.1.3→2025.1.4, Next.js 14.2.5→14.2.35. 라인을 넘지 않습니다.
- 프레임워크 관리 의존성은 그 최신 패치의 BOM·peer 범위·SDK manifest가 선언한 버전으로 정렬합니다. 현재 설치된 구 버전을 그대로 두지 않습니다.
- 비관리 직접 의존성은 manifest의 기존 선언 범위 또는 같은 major 안의 최신 안정 버전으로 갱신합니다. npm은 `wanted`, pnpm·yarn은 도구의 범위 내 후보, Flutter는 `resolvable`, Python은 제약을 만족하는 후보를 씁니다. exact로 고정된 Maven·npm·pip 버전은 같은 major 안에서 버전 문자열을 갱신합니다.
- 프레임워크 패치·BOM 버전은 바뀔 수 있습니다. 범위 기반 의존성은 `^`·`~` 표기를 유지하고, exact로 고정된 의존성은 같은 major 안에서 버전 문자열을 갱신합니다. Expo·Flutter SDK처럼 프레임워크 도구가 고정 버전에 맞추기 위해 manifest를 바꾸는 경우는 예외로 기록합니다.
- 현재 라인의 최신 패치가 이미 설치돼 있으면 그때만 유지합니다. 이것은 "버전 고정"이 아니라 "라인 안 최신"입니다.
- 현재 라인이 EOL이거나 보안 지원이 끝났으면 라인의 마지막 패치까지만 적용하고, "라인 업그레이드 필요"를 별도 결정으로 올립니다. 구 버전 라인을 조용히 고정하지 않습니다.
- exact로 고정된 Python 요구사항도 같은 major 안의 최신 안정으로 갱신합니다. major를 넘는 `==` 변경은 모드 3입니다. Go·Cargo는 도구의 기본 비파괴 업데이트를 모드 1로 봅니다.
- 범위 안 최신화가 CVE를 모두 없애지는 않습니다. 남은 CVE가 있으면 모드 2 승격을 제안합니다.
- production과 development를 구분해 보고합니다. 사용자가 요청하지 않으면 둘 다 포함합니다.

### 모드 2

- 모드 1의 결과(현재 라인 최신 안정 패치)를 먼저 계산하고 적용합니다.
- 그 상태에서도 남은 직접 의존성의 취약점을 audit 도구나 OSV로 확인합니다.
- 모드 1의 최신 라인 패치가 이미 고친 CVE는 다시 재정의하지 않습니다. 남은 취약점만 최소 수정 버전으로 목표를 올립니다.
- 수정 버전이 현재 프레임워크 라인 안이면 예외로 기록하고 재정의합니다. 프레임워크가 관리하지 않는 의존성은 CVE 수정을 위해 해당 패키지의 major를 넘을 수 있으며, 이 경우도 변경 사유를 기록합니다.
- 수정 버전이 현재 라인 밖(프레임워크 minor/major 업그레이드)을 요구하면 자동 적용하지 않고 결정 게이트로 올립니다. 예: Next.js 14의 일부 CVE가 15.5.28에서만 수정되는 경우, 15로 올릴지 14에서 가능한 만큼만 고칠지 사용자와 정합니다.
- 라인 최신 패치를 적용할 수 없는 사유가 있으면 개별 override와 패치 적용을 비교합니다. BOM 업그레이드는 지원 경로지만 변경 범위가 넓고, 개별 override는 최소 변경이지만 BOM 이탈을 추적해야 합니다. 예: Spring Boot BOM 패치가 Tomcat/Jackson CVE를 고치는 경우 `tomcat.version` override와 Boot 패치를 비교합니다.
- 수정 버전이 없으면 강제로 올리지 말고 "수정 버전 없음"으로 보고합니다.
- 전이 의존성만 취약하면 직접 부모를 올려 해결되는지 먼저 봅니다. resolution·override를 추가해야 하면 별도 결정으로 올립니다.
- 적용 후 같은 audit를 다시 실행해 취약점이 사라졌는지 확인합니다.

### 모드 3

- 모든 직접 의존성을 최신 안정 버전으로 올립니다.
- 프레임워크와 패밀리는 함께 올립니다. Angular는 `ng update`, Expo는 SDK 업그레이드와 `expo install`, Spring Boot는 parent/BOM 버전, Flutter는 SDK·`pub upgrade --major-versions` 같은 공식 경로를 씁니다.
- peer 충돌이 나면 `--force`나 `--legacy-peer-deps`로 덮지 않습니다. 패밀리를 함께 올리거나, 충돌 패키지를 유지하고 보고합니다.
- major 변경은 별도 변경으로 나누는 것을 권장합니다. 한 번에 여러 major를 섞으면 실패 원인을 찾기 어렵습니다.
- 전체 테스트와 프레임워크 진단을 통과하기 전에는 완료로 보고하지 않습니다.

### 예시

2026-10-28 기준 Next.js 14.2.5 + React 18.2.0 + lodash 4.17.20 프로젝트를 확인한 예입니다. 실제 판단은 저장소의 현재 도구 출력으로 다시 합니다.

| 패키지 | 현재 | 모드 1 | 모드 2 | 모드 3 |
| --- | --- | --- | --- | --- |
| next | 14.2.5 | 14.2.35 (14.x 최신 패치) | 14.2.35의 CVE를 모두 고치려면 15.5.28이 필요해 결정 게이트 | 16.4.3 |
| react | 18.2.0 | 18.3.1 (Next peer `^18.2.0` 범위) | 18.3.1 | 19.3.1 |
| lodash | 4.17.20 | 4.18.1 (선언 범위 내) | 4.18.1 (CVE 수정) | 4.18.1 |

- 모드 1은 Next를 14.x 라인의 최신 패치로 올리고, React를 프레임워크가 허용한 18.x 안에서 정렬합니다. Next 15/16으로 넘지 않습니다.
- 모드 2는 lodash를 고치지만, Next의 모든 CVE를 고치려면 15.5.28이 필요하므로 라인 업그레이드 결정으로 멈춥니다.
- 모드 3은 Next 16과 React 19를 함께 올리는 별도 작업입니다. peer 충돌과 빌드 실패를 확인해야 합니다.

Spring Boot 4.1.x + Spring Cloud 2025.1.x 예:

| 패키지 | 현재 | 모드 1 | 모드 2 | 모드 3 |
| --- | --- | --- | --- | --- |
| Spring Boot | 4.1.1 | 4.1.2 | 4.1.2 | 4.1.2 |
| Spring Cloud | 2025.1.3 | 2025.1.4 | 2025.1.4 | 2025.1.4 |
| guava | 30.0-jre | 30.1.1-jre (CVE 3건 남음) | 33.7.2-jre (CVE 0건) | 33.7.2-jre (CVE 0건) |
| uuid-creator | 4.0.0 | 4.6.1 | 4.6.1 | 6.1.1 |

- 모드 1의 Boot/Cloud 패치가 Tomcat/Jackson CVE를 BOM으로 고칩니다. 하지만 guava 30.1.1은 30.x 최신이어도 CVE가 남습니다.
- 모드 2는 guava만 33.7.2로 재정의해 CVE를 없앱니다. Boot/Cloud는 모드 1과 같습니다.
- 모드 3은 uuid-creator를 4.6.1에서 6.1.1로 major 업그레이드합니다. CVE와 무관한 변경입니다.

## 생태계별 확인·적용

도구가 없으면 아래 `## 도구 설치` 원칙에 따라 자동 설치를 시도하고, 실패하면 사용할 수 있는 대체 도구나 레지스트리 조회를 안내합니다.

| 생태계 | 현재·후보 확인 | 적용 | 검증 |
| --- | --- | --- | --- |
| npm | `npm outdated`, `npm ls --depth=0` | `npm update`, `npm install pkg@version` | `npm run build`, `npm test`, `npm audit` |
| pnpm | `pnpm outdated`, `pnpm list --depth 0` | `pnpm update`, `pnpm add pkg@version` | 스크립트 실행, `pnpm audit` |
| yarn | `yarn outdated`, `yarn list --depth=0` | `yarn upgrade`(v1), `yarn up`(berry), `yarn add` | 스크립트 실행, `yarn audit` |
| pip | `pip list --outdated`, `pip check` | requirements 수정 후 `pip install -r` | `pytest`, `pip check`, `pip-audit` |
| Poetry | `poetry show --outdated` | `poetry update`, `poetry add` | `poetry check`, 테스트 |
| uv | `uv pip list --outdated`, `uv lock --check` | `uv lock --upgrade-package`, `uv sync` | 테스트, `uv lock --check` |
| Flutter | `flutter pub outdated`, `flutter pub deps` | `flutter pub upgrade`, 모드 3은 `--major-versions` | `flutter analyze`, `flutter test` |
| Maven | `mvn versions:display-dependency-updates`, `mvn dependency:tree` | BOM·parent 버전 또는 선언 수정 | `mvn verify` |
| Gradle | `gradle dependencyUpdates`(플러그인), `gradle dependencies` | BOM·platform 또는 선언 수정 | `gradle test` |
| .NET | `dotnet list package --outdated --vulnerable` | `dotnet add package` | `dotnet test` |
| Go | `go list -m -u all`, `govulncheck ./...` | `go get module@version`, `go mod tidy` | `go test ./...` |
| Cargo | `cargo update --dry-run`, `cargo tree`, `cargo audit` | `cargo update`, `cargo add` | `cargo test`, `cargo audit` |
| Bundler | `bundle outdated`, `bundle audit` | `bundle update --conservative`, `bundle update` | `bundle exec rake test` |
| Composer | `composer outdated --direct`, `composer audit` | `composer update vendor/pkg` | 테스트 |

- 위 명령은 시작점입니다. 저장소의 스크립트와 CI가 실제 기준입니다.
- 도구 버전에 따라 하위 명령이 다를 수 있으므로 `--help`로 확인합니다.
- `npm outdated`의 `wanted`처럼 "현재 선언 범위 안 후보"를 제공하는 값은 비관리 의존성의 모드 1에 씁니다. `latest`는 모드 3에만 씁니다. 프레임워크 본체는 현재 라인의 최신 패치를 별도로 확인합니다.

## CVE 검증

- 생태계 audit를 우선합니다. 없으면 `osv-scanner scan source -r .`처럼 lockfile을 읽는 도구를 쓰고, 그것도 없으면 OSV API로 직접 의존성의 패키지·버전을 조회합니다.
- 결과에는 취약점 ID, 심각도, 현재 버전, 수정 버전, 조치를 적습니다.
- 최소 수정 버전을 목표로 합니다. 최신 버전이 항상 필요한 것은 아닙니다.
- 수정 버전이 major뿐이면 별도 결정으로 올립니다. 프레임워크 관리 패키지라면 프레임워크 업그레이드와 함께 검토합니다.
- 수정 버전이 프레임워크 major 업그레이드를 요구하면 모드 2로 자동 진행하지 않고, 현재 major에서 가능한 수정과 major 업그레이드 중 무엇을 할지 결정받습니다.
- audit 도구가 없거나 네트워크가 없으면 "CVE 미확인"으로 보고합니다. 취약점이 없다고 단정하지 않습니다.
- 보안 상세는 내부 보고에만 적고, 고객 문서에는 공격 방법을 쓰지 않습니다.

## 출력 형식

계획은 채팅에 아래 표로 보여 줍니다.

| 패키지 | 현재 | 기준 라인 후보 | 최신 | 관리 | CVE | 목표 | 조치 | 위험 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

- `기준 라인 후보`는 현재 언어·프레임워크 라인 안의 최신 안정 패치입니다. 모드 1의 기준입니다.
- `최신`은 라인 밖까지 포함한 최신 안정 버전입니다. 모드 3에서만 씁니다.

- `관리`에는 관리 주체와 근거를 적습니다. 예: "Next.js peer", "Spring BOM", "없음".
- `조치`는 유지·갱신·재정의·검토·건너뜀 중 하나입니다.
- `위험`은 patch/minor/major와 프레임워크 이탈 여부를 함께 봅니다.
- 적용 명령과 검증 명령을 표 아래에 적습니다.

적용 후 보고:

- 바뀐 패키지와 버전
- 유지한 패키지와 이유
- 수정한 CVE와 수정 버전
- 실행한 검증과 결과
- 실패·미확인 항목
- 롤백 방법

사용자가 원하면 `docs/dependencies/update-YYYY-MM-DD.md`에 같은 내용을 기록합니다. 이 파일은 저장소 정책에 따라 커밋 여부를 정합니다.

## 실패 처리

- 프레임워크 관리 근거를 찾지 못하면 추측하지 말고 관리하지 않는 것으로 두되, 가정을 계획에 적습니다.
- 현재 프레임워크 라인이 EOL이거나 보안 지원이 끝났으면 모드 1의 라인 최신 패치까지만 적용하고, 라인 업그레이드를 별도 결정으로 올립니다.
- outdated 도구가 없으면 아래 `## 도구 설치` 원칙에 따라 자동 설치를 시도하고, 실패하면 레지스트리 조회나 manifest 비교로 대체합니다. 패키지 매니저 자체를 임의로 바꾸지 않습니다.
- audit 도구가 없으면 아래 `## 도구 설치` 원칙에 따라 자동 설치를 시도하고, 실패하면 OSV API나 `osv-scanner`를 안내합니다. 둘 다 불가능하면 CVE 미확인으로 남깁니다.
- peer 충돌이 나면 `--force`로 넘기지 않습니다. 패밀리 업데이트, 버전 유지, 별도 결정 중 하나를 제안합니다.
- 빌드·테스트가 실패하면 해당 패키지 또는 변경 묶음을 되돌리고 실패 로그를 보고합니다. 전체를 성공으로 포장하지 않습니다.
- lockfile 충돌은 패키지 매니저로 다시 생성합니다. 손으로 병합하지 않습니다.
- 모노레포에서 루트만 보고 판단하지 않습니다. 앱별 manifest와 lockfile을 확인합니다.
- 테스트가 없는 저장소는 빌드·린트·타입 검사까지 수행하고, 테스트 미실행을 명시합니다.
- 모드 3에서 프레임워크가 깨지면 모드 1로 되돌릴 수 있는지 확인하고, 롤백 명령을 안내합니다.

## 도구 설치

필요한 프로그램이 없으면 자동 설치를 시도합니다.

- OS 패키지 관리자(macOS `brew`, Debian/Ubuntu `apt-get`, Fedora `dnf`, Arch `pacman`, Windows `winget`·`choco`·`scoop`)와 언어 패키지 관리자(`uv`·`pipx`·`npm`·`cargo`·`go`)를 우선합니다.
- 작업에 필요한 도구만 설치합니다. 무관한 패키지나 전체 도구 묶음을 설치하지 않습니다.
- 설치 전에 도구와 명령을 알립니다. 사용자가 설치를 거부하면 설치하지 않고 대체 도구나 입력 파일을 요청합니다.
- 사용자 권한 설치를 우선합니다. `sudo`가 필요하면 `sudo -n`으로만 시도하고 암호 입력을 요구하지 않습니다. 실패하면 실행할 명령과 이유를 보고합니다.
- 공식 패키지·저장소만 사용합니다. `curl | sh`, 출처 불명 바이너리, 임의 URL 다운로드·실행을 금지합니다.
- 설치 후 `command -v`와 `--version`으로 확인합니다. 실패하면 대체 도구를 쓰거나 입력 파일을 요청합니다.
- 설치한 도구·버전·실패 사유를 결과나 evidence에 기록합니다.
- 문서·고객 데이터를 설치 과정에서 외부로 보내지 않습니다.
- GUI 앱·드라이버·커널·서비스처럼 시스템 변경이 큰 설치는 먼저 확인합니다.

## 금지

- 사용자 선택 없이 모드 3을 적용하지 않습니다.
- 모드 1에서 현재 프레임워크 라인을 넘거나, BOM·peer 범위를 벗어난 버전으로 올리지 않습니다. 라인 밖 변경은 모드 2 예외 또는 모드 3으로만 합니다.
- CVE 재정의를 조용히 하지 않습니다. 대상·이유·범위 밖 여부를 기록합니다.
- `--force`, `--legacy-peer-deps`, `--ignore-engines`로 충돌을 덮지 않습니다. 사용자가 명시적으로 승인한 경우에만 씁니다.
- lockfile을 직접 편집하지 않습니다.
- canary·beta·RC를 "최신 안정"으로 부르지 않습니다.
- 확인하지 않은 CVE를 "없음"으로 보고하지 않습니다.
- 한 커밋에 여러 생태계의 무관한 업데이트를 섞지 않습니다.
- 사용자 지시 없이 커밋·푸시·PR·릴리스를 하지 않습니다.
- 프로젝트 의존성 업그레이드를 확인 없이 실행하지 않습니다. 도구 설치는 `## 도구 설치` 원칙을 따릅니다.
