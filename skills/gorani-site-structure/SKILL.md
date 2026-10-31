---
name: gorani-site-structure
description: 실제 프론트 화면의 메뉴·탭·레이아웃을 확인해 사이트 구조도 산출물을 만든다. Excel·Markdown·HTML과 화면·API only·표준 근거를 정리한다. IA 문서화, 메뉴 구조 검토, 화면 목록 작성이 필요할 때 사용.
---

# 사이트 구조도 생성

실제 프론트 화면에서 확인한 **메뉴·탭·레이아웃**을 기준으로 사이트 구조도와 화면 목록을 만듭니다. API 목록은 구조의 근거가 아니며, 화면별 API 연결과 API only 부록으로만 사용합니다.

## 전제

- 사이트 구조의 원천은 **실제 렌더링된 프론트**입니다. API 스펙이나 URL만으로 구조를 만들지 않습니다.
- 로그인·역할별 메뉴 노출 차이가 있으면 테스트 계정과 역할을 확인합니다.
- 데스크톱·모바일 메뉴가 다르면 두 화면 폭을 모두 확인합니다.
- 스크린샷은 엑셀에 삽입하지 않고 `screens/` 아래 파일 경로만 기록합니다.
- HTML은 자기완결 페이지로 만들고 외부 CSS·JS·폰트·이미지를 쓰지 않습니다.
- `xlsx`를 선택할 때만 `openpyxl`이 필요합니다.
- Playwright 자동 수집은 선택 사항입니다. 권한·세션·소요 시간 때문에 기본은 에이전트가 브라우저로 실제 화면을 확인합니다.

## 기준

한국 공공 가이드를 기본 기준으로 사용합니다.

- KRDS 디지털 정부서비스 UI/UX 가이드라인 (2025.8)
  - 메인 메뉴는 서비스 정보 구조를 반영하고 최대 3수준
  - 현재 페이지는 활성 메뉴로 표시
  - LNB·SNB는 IA가 많고 depth가 깊은 화면에 사용
  - 모바일은 햄버거·사이드 탭·집중 탐색 레이어 등 별도 패턴
  - 키보드 탐색, 메뉴 계층 구조, `aria-current` 제공
- 전자정부 웹사이트 품질관리 지침 (2025.6.25.)
  - 공공 웹사이트 품질 기준과 준수 항목 확인

산출물의 `표준 근거` 시트에 실제 적용 항목과 원문 링크를 기록합니다.

## 절차

1. 사이트 URL, 테스트 계정, 확인할 역할(admin·owner·member 등), 화면 폭(desktop·mobile), Playwright 사용 여부를 확인합니다.
2. 실제 프론트를 엽니다. 로그인 세션을 준비하고 역할별로 메뉴가 어떻게 보이는지 확인합니다.
3. 전역 내비게이션을 확인합니다.
   - 사이드바, 헤더, GNB, LNB
   - 하위 메뉴, 탭, 브레드크럼
   - 현재 페이지 활성 메뉴
   - 모바일 햄버거·사이드 탭·집중 탐색 레이어
4. 화면을 순회하며 다음을 기록합니다.
   - 화면 ID, 화면명
   - 실제 메뉴 경로(`menu_path`)
   - 부모 화면(`parent_id`)
   - URL 패턴
   - 레이아웃 유형
   - 접근 역할
   - 노출 방식(전역 메뉴·하위 메뉴·상세 진입·탭·액션·모달·숨김)
   - 데스크톱·모바일 노출
   - 상태(active·planned·deprecated)
   - 스크린샷 경로
   - 화면에서 호출하는 API
5. 메뉴 depth는 실제 메뉴 성격만 기록합니다.
   - 최소 2Depth는 항상 유지
   - KRDS 기준 최대 3Depth
   - 3Depth를 넘는 상세·탭·액션 화면은 depth가 아니라 `parent_id`와 `exposure`로 표현
6. API만 있고 화면이 없는 경로는 `api_only`에 분리합니다.
7. `site-structure-input.json`을 작성하고 검증합니다.

   `python3 <스킬 폴더>/scripts/site_structure.py --input docs/site-structure/site-structure-input.json --outdir docs/site-structure --name site-structure --formats xlsx,md,html`

8. 사용자가 고른 형식만 생성합니다. 기본은 `xlsx,md,html`입니다.
9. 출력의 화면 수, depth, API 매핑, API only, 표준 근거, 검토 메모를 확인합니다.
10. `--strict`를 주면 검증 경고가 있을 때 exit 1로 CI에서 차단할 수 있습니다.

## 입력 JSON

최상위:

- `site`: 사이트명
- `base_url`: 기준 URL
- `inspected_at`: 실제 화면 확인 시점
- `source`: 수집 기준. 예: `렌더링된 프론트 레이아웃`
- `standard`: 적용 기준 문서
- `roles`: 확인한 역할 목록
- `viewports`: 확인한 화면 폭 목록
- `review_status`: 검토 상태
- `pages`: 화면 목록
- `api_only`: 화면 없이 API만 있는 경로
- `standards`: 표준 근거
- `warnings`: 검토 메모

`pages` 필드:

- `id`: 화면 ID. 중복 금지
- `title`: 화면명
- `menu_path`: 실제 메뉴 경로 배열. 예: `["사용자", "사용자 목록"]`
- `parent_id`: 상세·탭·액션 화면의 부모 화면 ID
- `url`: URL 패턴. 예: `/users/[id]`
- `layout`: `list`, `detail`, `form`, `dashboard`, `settings` 등
- `roles`: 접근 역할 배열
- `exposure`: 노출 방식
- `desktop`, `mobile`: 노출 여부
- `status`: `active`, `planned`, `deprecated`
- `screenshot`: `screens/...png` 상대 경로
- `apis`: `method`, `path`, `purpose`, `when`, `note`
- `source`: 프론트 소스 경로(선택)
- `note`: 비고

`api_only` 필드:

- `method`, `path`, `purpose`, `caller`, `reason`, `note`

`standards` 필드:

- `source`, `name`, `scope`, `rule`, `url`

`warnings` 필드:

- `category`, `message`, `action`

## 출력 형식

- `site-structure.xlsx`:
  - `요약`: 사이트·검사 시점·적용 기준·Depth 규칙·화면/API/표준/검토 집계
  - `사이트 구조`: 실제 메뉴 depth 컬럼, 부모 화면, 노출, URL, 역할, 데스크톱·모바일, 상태, 스크린샷 경로
  - `화면 목록`: 화면별 상세
  - `API 매핑`: 화면과 API 호출의 연결
  - `API only`: 화면 없이 API만 있는 경로. 구조도와 분리
  - `표준 근거`: KRDS·전자정부 품질관리 지침의 적용 항목
  - `검토 메모`: 확인 필요 사항과 가정
- `site-structure.md`: 같은 내용의 Markdown 표
- `site-structure.html`: 검색·메뉴 트리·화면 표·표준 근거·검토 메모를 담은 자기완결 HTML
- `--formats md` 또는 `html`만 주면 openpyxl 없이 동작합니다.

## 검증

- 실제 메뉴 항목이 구조도에 모두 있는지 확인
- 화면별 스크린샷 경로가 실제 파일과 맞는지 확인
- 역할·화면 폭별 메뉴 차이가 반영됐는지 확인
- 상세·탭·액션 화면이 부모 화면으로 연결됐는지 확인
- 3Depth 초과 메뉴가 없는지 확인. 있으면 경고를 남기고 메뉴가 아닌 화면으로 분리
- API only가 구조도에 섞이지 않았는지 확인
- HTML 검색과 메뉴 트리, 외부 요청 0건, CSP 확인
- Excel 시트·필터·스크린샷 경로 열 확인

## 실패 처리

- 입력 JSON이 없거나 `pages`가 비어 있으면 중단합니다.
- `page.id`가 중복되거나 `status`가 허용 값이 아니면 중단합니다.
- `parent_id`가 없으면 경고하고 부모 화면을 비웁니다.
- `active` 화면에 스크린샷 경로가 없으면 경고합니다.
- 메뉴 depth가 3을 넘으면 KRDS 기준 경고를 남깁니다.
- `xlsx`를 선택했는데 openpyxl이 없으면 설치를 시도합니다. 거부하면 `--formats md` 또는 `html`로 생성합니다.
- API만 보고 화면을 만들지 않습니다. 실제 화면을 확인할 수 없으면 해당 화면은 `planned` 또는 `미확인`으로 두고 검토 메모에 남깁니다.
- Playwright 자동 수집이 실패하면 세션·권한·동적 렌더링을 확인하고, 에이전트가 브라우저로 직접 보정합니다.

## 도구 설치

필요한 프로그램이 없으면 자동 설치를 시도합니다.

- `xlsx`: `openpyxl`
- Playwright를 선택한 경우: `playwright`와 브라우저 바이너리
- OS 패키지 관리자와 언어 패키지 관리자를 우선하고, 필요한 도구만 설치합니다.
- 설치 전에 도구와 명령을 알립니다. 사용자가 거부하면 설치하지 않고 대체 형식이나 입력 파일을 요청합니다.
- 공식 패키지·저장소만 사용합니다. `curl | sh`, 출처 불명 바이너리, 임의 URL 실행을 금지합니다.
- 설치 후 `command -v`와 `--version`으로 확인합니다.
- 설치한 도구·버전·실패 사유를 결과나 evidence에 기록합니다.

## 금지

- API 스펙이나 URL만 보고 화면 구조를 만들지 않습니다.
- 실제 화면에 없는 화면·메뉴·탭을 추측해 넣지 않습니다.
- 스크린샷을 엑셀에 삽입하거나 외부 이미지로 대체하지 않습니다. 파일 경로만 씁니다.
- 서비스 코드·라우트·DB를 수정하지 않습니다.
- 고객 정보, 내부 URL, 시크릿을 문서에 넣지 않습니다.
- 사용자 지시 없이 커밋·푸시·PR을 만들지 않습니다.
- 경고를 숨기기 위해 결과를 임의로 편집하지 않습니다.
