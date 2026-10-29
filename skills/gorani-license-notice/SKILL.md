---
name: gorani-license-notice
description: 앱이나 백엔드에 게시할 오픈소스 고지 페이지를 SBOM과 패키지의 LICENSE·NOTICE 원문에서 자동 생성한다. 전체 고지 페이지와 이름·버전·GitHub 라이선스 링크만 담은 간소화 페이지를 지원한다. 앱 배포 전 고지 의무 확인, 서드파티 라이선스 목록 작성, copyleft 검토가 필요할 때 사용.
---

# 오픈소스 고지 페이지 생성

앱에 포함된 오픈소스의 저작권 표시와 라이선스 전문을 모아, 앱 WebView나 백엔드에서 바로 제공할 수 있는 자기완결 HTML 페이지로 만듭니다.

## 전제

- python3 가 필요합니다. HTML 과 md 생성은 표준 라이브러리만 사용합니다.
- SBOM 생성을 위해 `syft` 가 필요합니다. 없으면 아래 `## 도구 설치` 원칙에 따라 자동 설치를 시도합니다.
- 라이선스 전문은 설치된 패키지 디렉터리에서 읽습니다. npm·pnpm·pub·python 패키지가 설치되어 있어야 하며, 설치하지 않았다면 전문이 비고 검토 목록에 남습니다.
- 앱에 실제로 포함되는 패키지만 대상으로 하려면 운영 의존성만 설치한 상태에서 수집합니다. 예: `npm ci --omit=dev`
- `xlsx` 산출물을 선택할 때만 openpyxl 이 필요합니다. 없으면 아래 `## 도구 설치` 원칙에 따라 자동 설치를 시도합니다.
- 이 스킬은 라이선스 판단을 대신하지 않습니다. copyleft 와 미확인 라이선스는 검토 목록으로 넘깁니다.

## 절차

1. 대상 앱과 패키지 매니저를 확인합니다. 모노레포라면 저장소 루트가 아니라 앱 디렉터리에서 수집합니다. 앱 버전을 확인할 수 없으면 추측하지 말고 사용자에게 묻습니다. 함께 생성할 산출물(html, md, review, xlsx)과 간소화 페이지(`--simple`) 여부도 확인합니다.
2. 작업 디렉터리를 만듭니다. SBOM 과 중간 JSON 은 `.legal/` 에 두고, 저장소 정책에 따라 `.gitignore` 에 추가합니다. 이미 커밋된 파일은 건드리지 않습니다.
3. SBOM 을 만듭니다. `syft dir:. -o cyclonedx-json=.legal/sbom.cdx.json`
4. 운영 범위를 기록합니다. npm 이면 `npm ls --omit=dev --all --json > .legal/runtime.json` 을 실행합니다. peer 의존성 문제로 종료 코드가 1이어도 JSON 이 만들어졌는지 먼저 확인합니다.
5. 라이선스 정보를 수집합니다. `python3 <스킬 폴더>/scripts/collect_licenses.py --sbom .legal/sbom.cdx.json --root . --runtime .legal/runtime.json --out .legal/licenses-input.json`
6. 수집 결과를 확인합니다. 출력의 `packages`, `missing_text`, `runtime`, `dev`, `unknown_scope`, `unknown_license` 를 읽고 다음을 처리합니다.
   - `missing_text` 가 0보다 크면 해당 패키지가 설치되어 있는지, 패키지에 LICENSE 파일이 실제로 있는지 확인합니다.
   - `unknown_license` 가 0보다 크면 패키지 메타데이터나 원본 저장소에서 확인해 입력 JSON 의 `license` 를 보정합니다. 확인할 수 없으면 unknown 으로 남깁니다.
   - 개발 의존성이 섞였으면 `--runtime` 을 지정해 다시 수집하거나, 생성 단계에서 `--exclude-dev` 를 씁니다.
7. 고지 페이지를 생성합니다. `python3 <스킬 폴더>/scripts/notice_build.py --input .legal/licenses-input.json --outdir docs/licenses --name third-party-notices --formats html,md,review`. 사용자가 고른 형식만 `--formats`에 넣습니다.
   - 간소화 페이지: 같은 명령에 `--simple`을 붙입니다. 기본은 `third-party-notices-simple.html`, `.md`이고, `--formats html` 또는 `--formats md`로 하나만 만들 수 있습니다.
8. 앱이나 백엔드에 연결합니다. HTML 은 외부 요청 없이 동작하므로 앱 자산에 넣거나 정적 파일로 제공합니다.
9. 검증합니다. 브라우저에서 데스크톱·모바일 폭으로 열어 검색과 라이선스 전문 표시를 확인하고, 네트워크 요청이 없는지 확인합니다.
10. 의존성이 바뀔 때마다 다시 생성합니다. 릴리스 체크리스트나 CI 에 `--fail-on-review` 를 넣으면 검토 항목이 있는 상태로 배포되는 것을 막을 수 있습니다.

## 입력 JSON

`collect_licenses.py` 가 만들고 `notice_build.py` 가 읽습니다. 누락을 보정할 때만 직접 수정합니다.

- 최상위: `project`, `app_version`, `generated_at`, `ecosystem`, `packages`, `logs`
- 패키지 필수: `name`, `version`, `license`, `license_text`
- 패키지 선택: `copyright`, `purl`, `repository`, `scope`(runtime/dev/unknown), `dependency`(direct/transitive), `license_source`, `license_url`, `notice_text`
- `repository`는 간소화 페이지의 GitHub 링크를 만드는 데 씁니다. `license_source`는 링크에 넣을 라이선스 파일명을 정하는 데 씁니다.
- `license` 는 SPDX 식별자를 우선 사용합니다. `MIT OR Apache-2.0` 같은 표현을 지원합니다.
- `license_text` 는 원문 그대로 둡니다. 요약·번역·형식 변경 금지.
- `copyright` 는 여러 줄을 허용합니다. 수집기는 최대 3줄을 추출합니다.
- `logs` 는 `tool`, `command`, `status`, `note` 로 구성합니다.

## 고지 의무 분류

| 분류 | 해당 라이선스 | 의미 | 페이지 |
| --- | --- | --- | --- |
| none | 0BSD, MIT-0, Unlicense, CC0-1.0, WTFPL | 고지 의무 없음 | 목록에는 포함 |
| notice | MIT, ISC, BSD-2-Clause, BSD-3-Clause, Apache-2.0, Zlib, BSL-1.0, Python-2.0 | 저작권·라이선스 고지 | 포함 |
| weak | MPL-2.0, EPL-2.0, CDDL-1.0, LGPL-2.1, LGPL-3.0 | 파일 단위·링크 예외 검토 | 포함 + 검토 |
| strong | GPL-2.0, GPL-3.0 | 소스 공개 범위 검토 | 포함 + 검토 |
| network | AGPL-3.0 | 네트워크 제공 시 소스 공개 검토 | 포함 + 검토 |
| unknown | 확인되지 않음 | 배포 전 확인 필요 | 포함 + 검토 |

- `OR` 은 더 약한 쪽을 택합니다. 예: `MIT OR GPL-3.0-only` 는 notice.
- `AND` 는 더 강한 쪽을 택합니다. 예: `MIT AND GPL-3.0-only` 는 strong.
- 식에 unknown 이 섞이면 전체를 unknown 으로 둡니다.
- `OR`·`AND` 표현은 분류와 별개로 검토 목록에 남겨, 배포에 적용할 라이선스와 수록된 전문이 맞는지 확인합니다.
- 이 표는 시작점입니다. weak·strong·network 는 법무 검토 없이 허용으로 단정하지 않습니다.

## 출력 형식

생성할 산출물은 사용자에게 먼저 묻고 `--formats`로 지정합니다. 기본은 `html,md,review`이고, `xlsx`는 요청할 때만 만듭니다.

| 형식 | 파일 | 용도 |
| --- | --- | --- |
| html | `third-party-notices.html` | 앱 WebView·백엔드에 게시하는 자기완결 페이지 |
| md | `third-party-notices.md` | diff 검토, 앱스토어 제출 자료 |
| review | `third-party-notices-review.md` | 내부 검토 목록. 검토 항목이 있을 때만 생성 |
| xlsx | `third-party-notices.xlsx` | 내부 검토용 엑셀. openpyxl 필요 |

사용자에게는 짧게 이렇게 묻습니다. "고지 산출물을 선택해 주세요. 기본은 HTML·md·검토 목록입니다. 엑셀도 필요하신가요?"

- 선택한 형식만 생성하거나 갱신합니다. 선택하지 않은 기존 파일은 건드리지 않습니다.
- `--xlsx`는 `--formats`에 xlsx를 추가하는 별칭으로 계속 쓸 수 있습니다.
- `review` 없이 `html`만 선택해도 검토 항목 수는 요약에 표시됩니다. 검토 사유가 필요하면 `review`를 포함합니다.

### 간소화 페이지

`--simple`(또는 `--minimal`)을 붙이면 라이선스 전문·저작권·검토 목록 없이 **의존성 이름, 버전, GitHub 라이선스 링크**만 담은 페이지를 만듭니다.

- 출력: `third-party-notices-simple.html`, `third-party-notices-simple.md`
- 기본은 두 형식입니다. `--formats html` 또는 `--formats md`로 하나만 선택할 수 있습니다.
- 각 행은 의존성 이름, 버전, GitHub의 라이선스 파일 링크만 포함합니다.
- `license_url`이 있으면 그 링크를 우선 사용합니다. 없으면 `repository`가 GitHub URL일 때 `https://github.com/<owner>/<repo>/blob/HEAD/<license file>`로 만듭니다.
- `<license file>`은 `license_source`의 파일명을 쓰고, 없으면 `LICENSE`를 씁니다.
- GitHub 저장소가 없거나 GitHub URL이 아니면 링크를 `-`로 표시하고, 출력 요약의 `missing_github_links`에 집계합니다.
- `--simple`은 `review`·`xlsx`와 함께 쓸 수 없습니다. `--fail-on-review`는 계속 동작합니다.
- 간소화 페이지는 전체 고지 의무를 대체하지 않습니다. 배포에는 전체 HTML을 사용하고, 간소화 페이지는 사내 목록이나 링크 모음 용도로만 씁니다.

HTML:

- 단일 파일입니다. CSS 와 JavaScript 를 인라인으로 넣고 외부 CDN·폰트·이미지를 쓰지 않습니다.
- `Content-Security-Policy` 로 외부 요청을 막습니다. 앱 WebView 와 오프라인 환경에서 그대로 열립니다.
- 구성: 프로젝트·버전·생성일, 패키지 검색, 라이선스 목차, 라이선스별 섹션.
- 패키지마다 이름, 버전, 저작권 표시를 보여 주고 라이선스 전문은 접힌 상태로 둡니다.
- 같은 라이선스 전문은 저작권 줄·줄바꿈·따옴표 같은 표기 차이를 무시하고 한 번만 수록합니다. 패키지별 저작권은 각 패키지에 표시합니다.
- 전문을 찾지 못한 패키지는 숨기지 않고 "License text not found" 로 표시합니다.
- 검토 목록은 HTML 에 넣지 않습니다. 앱 사용자에게 내부 검토 사유를 노출하지 않습니다.
- 라이트·다크 모드, 모바일 폭, 인쇄를 지원합니다.

md:

- HTML 과 같은 내용을 평문으로 담습니다. diff 검토와 앱스토어 제출 자료로 씁니다.
- 라이선스 전문은 코드 블록으로 원문 그대로 넣습니다.

review:

- `third-party-notices-review.md`: 패키지, 버전, 라이선스, 사유, 조치를 담은 한국어 표입니다. 검토 항목이 있을 때만 생성합니다.

xlsx:

- `third-party-notices.xlsx`: 시트는 요약, 패키지, 라이선스 전문, 검토 필요, 실행 로그입니다.
- `xlsx`를 선택한 경우에만 openpyxl이 필요합니다.

검토 파일과 엑셀은 내부용입니다. 앱 자산이나 배포 경로에 넣지 않습니다.

종료 코드:

- 정상 0
- `--fail-on-review` 를 주었고 검토 항목이 있으면 1. `review` 형식을 선택하지 않아도 게이트는 동작합니다.
- 입력·인자 오류는 argparse 기본값인 2

## 앱과 백엔드 연결

- 앱 WebView: HTML 을 앱 자산에 복사하고 로컬 파일로 엽니다. Android 는 `file:///android_asset/legal/third-party-notices.html`, iOS 는 번들 리소스, Flutter 는 assets 경로를 씁니다. 파일이 자기완결이므로 네트워크 권한이 필요 없습니다.
- 백엔드: 정적 파일로 두고 `/legal/third-party-notices` 같은 고정 경로로 제공합니다. `Content-Type: text/html; charset=utf-8` 을 지정하고 앱 버전과 함께 캐시 키를 둡니다.
- 앱 설정이나 정보 화면에 "오픈소스 라이선스" 링크를 추가합니다.
- `docs/licenses/` 를 원본으로 두고 배포 시 앱 자산이나 `public/` 으로 복사하는 방식을 권장합니다. 복사 단계가 있으면 릴리스 스크립트에 넣습니다.
- 검토 파일과 엑셀은 같은 디렉터리에 있어도 배포 대상에서 제외합니다.

## 검증

- HTML 을 데스크톱과 모바일 폭에서 열어 목차, 검색, 접기/펼치기를 확인합니다.
- 개발자 도구 네트워크 탭에서 외부 요청이 0건인지 확인합니다. CSP 가 `default-src 'none'` 이므로 요청이 생기면 CSP 위반으로 보입니다.
- SBOM 의 런타임 패키지 수와 페이지의 패키지 수가 같은지 확인합니다. `--exclude-dev` 를 썼다면 차이를 설명할 수 있어야 합니다.
- 검토 파일의 항목이 모두 처리되었거나, 남긴 항목은 담당자와 사유를 기록했는지 확인합니다.
- `--fail-on-review` 로 CI 에서 종료 코드 1이 나오는지 한 번 확인합니다.
- 간소화 페이지는 행마다 이름·버전·GitHub 링크만 있는지, 링크 없는 패키지가 `-`와 `missing_github_links`로 표시되는지 확인합니다.
- 앱 WebView 에서 JavaScript 가 꺼져 있어도 목록과 전문은 보여야 합니다. 검색만 동작하지 않습니다.

## 실패 처리

- `syft` 가 없으면 아래 `## 도구 설치` 원칙에 따라 자동 설치를 시도하고, 실패하면 중단합니다.
- SBOM 구성요소가 0이면 경로와 대상 디렉터리를 확인합니다. 모노레포 루트를 스캔했다면 앱 디렉터리로 다시 실행합니다.
- `npm ls` 결과를 읽을 수 없으면 `--runtime` 을 빼고 수집합니다. 이때 scope 는 unknown 이 되고 모든 패키지가 대상이 됩니다.
- 라이선스 전문이 없으면 원본 저장소의 LICENSE 를 받아 입력 JSON 의 `license_text` 에 넣습니다. 없는 채로 두면 페이지에 "License text not found" 로 표시되고 검토 목록에 남습니다.
- 라이선스를 확인할 수 없으면 unknown 으로 두고 검토합니다. 추측한 SPDX ID 를 넣지 않습니다.
- `xlsx`를 선택했는데 openpyxl 이 없으면 아래 `## 도구 설치` 원칙에 따라 자동 설치를 시도합니다. 설치를 거부하거나 실패하면 xlsx만 건너뛰고, 선택한 다른 형식은 그대로 사용합니다.
- `--fail-on-review` 로 종료 코드 1이 나오면 실패가 아니라 검토가 필요하다는 뜻입니다. 검토 파일을 확인하고, 남길 항목은 사유를 기록합니다.
- HTML 이 WebView 에서 깨지면 CSP 위반과 JavaScript 비활성 여부를 확인합니다. 정적 내용은 JavaScript 없이도 보여야 합니다.
- 간소화 페이지의 GitHub 링크가 비어 있으면 `repository`가 수집됐는지와 GitHub URL인지 확인합니다. 저장소를 확인할 수 없으면 링크를 만들지 말고 `-`로 둡니다.

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

- 라이선스 전문을 요약·번역·변형하지 않습니다.
- 라이선스를 추측해 채우지 않습니다. 확인할 수 없으면 unknown 으로 둡니다.
- 패키지를 자동으로 업그레이드하거나 소스를 수정하지 않습니다.
- 사용자 지시 없이 커밋·푸시·PR 을 만들지 않습니다.
- `-review.md` 와 `.xlsx` 를 앱 자산이나 공개 페이지에 포함하지 않습니다.
- 고지 페이지에 내부 URL, 시크릿, 고객 정보를 넣지 않습니다.
- 간소화 페이지를 전체 라이선스 고지 의무의 대체물로 배포하지 않습니다. 이름·버전·링크만으로는 저작권·전문 수록 의무를 충족하지 못할 수 있습니다.
- 외부 CDN, 웹폰트, 원격 스크립트를 넣지 않습니다. 자기완결성을 깨뜨립니다.
- copyleft 라이선스를 법무 검토 없이 "사용 가능"으로 단정하지 않습니다.
- 무관한 도구·패키지 설치, 출처 불명 설치를 하지 않습니다.
