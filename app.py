import os
import re
import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader
from google import genai
from google.genai import types
from notion_client import Client
import tempfile
import md2pdf_nonode
import markdown as mdlib
import streamlit.components.v1 as components

load_dotenv()

st.set_page_config(page_title="강의 자동 정리기", page_icon="📚", layout="wide")
st.markdown("""
<style>
  .stButton>button { border-radius: 8px; font-weight: 600; padding: 0.5rem 1.4rem; }
  h1 { letter-spacing: -0.5px; }
  [data-testid="stSidebar"] { background: #f7f9fc; }
  .block-container { padding-top: 2.2rem; }
</style>
""", unsafe_allow_html=True)

st.title("📚 강의 자동 정리기")
st.caption("강의 자료(텍스트·파일·PDF) → 내 가이드대로 자동 정리 · 품질검증 · PDF · 노션")

DEFAULT_GUIDE = """# 강의 → 독학 자료 PDF 변환 작업 가이드 (Claude용)

이 폴더는 강의 자료(클로바노트 텍스트, PDF 슬라이드, 칠판 사진 등)를 **수업을 전혀 듣지 않고도 이 파일 하나만으로 처음부터 공부할 수 있는 독학 자료(self-study material)**로 변환하는 파이프라인이다. 사용자가 강의 자료를 주면서 "PDF로 정리해줘"라고 하면 이 가이드를 따른다.

**핵심 전제 — 가장 중요:** 사용자는 수업을 직접 듣지 않으며, 강의 슬라이드·교재도 보지 않는다. 변환된 PDF 한 파일이 곧 교재이자 강의이다. 따라서 모든 개념은 그 주제에 처음 입문하는 독자도 이해할 수 있도록 자체 완결적으로(self-contained) 서술되어야 한다.

대상 과목은 정해져 있지 않다 — 수학, 통계, 컴공, 경제, 인문학 등 어떤 과목이든 적용 가능.

---

## 작업 흐름

1. **자료 확인** — 사용자가 어떤 파일을 줬는지 본다
   - `.txt` 파일: 클로바노트 음성 인식 텍스트 (말투 그대로, 오타 많음)
   - `.pdf` 파일: 강의 슬라이드 또는 강의자료
   - `.png/.jpg`: 칠판 사진, 필기 사진, 수업범위 이미지
   - `.md` 파일: 이미 정리된 마크다운 — 그러면 정리 단계 스킵하고 바로 변환

2. **수업범위·매핑 파일 우선 확인** — `수업범위.jpg`, `활용자료 모음.txt` 같은 메타 파일이 있으면 먼저 읽어서 녹음본 ↔ 슬라이드 매핑 파악

3. **내용 정리** — 클로바노트나 슬라이드 자료라면, 마크다운으로 정리 (아래 톤 가이드 참고)

4. **PDF 변환** — `./make-pdf.sh <입력.md> <출력.pdf>` 실행 (Chrome headless 사용)

---

## 정리 톤 가이드 — 매우 중요

**이 가이드의 표준이 곧 유일한 표준이다.** 별도 지시가 없으면 항상 아래의 깊이와 톤으로 작성한다. v1/v2 같은 버전 구분은 없다.

### 1. 강의 흐름과 내용 보존

- **내용 요약하지 않는다.** 강의에서 다룬 개념은 빠짐없이 담되, 독자가 처음 본다는 전제로 풀어 쓴다.
- **강의 순서를 임의로 바꾸지 않는다.** 교수님이 설명한 흐름을 그대로 유지한다. (단, 독학자료 관점에서 배경 설명이 빠진 경우 보충은 허용)
- **예시는 살린다.** 교수님이 개념 설명을 위해 든 사례·예제·응용은 학습에 중요하므로 그대로 정리한다.
- **수업 운영, 시험, 출석체크, 과제 안내 관련 내용은 반드시 별도 부로 정리한다.**
- **농담·여담·잡담은 뺀다.** 학습 본질과 무관한 사담은 제외한다.
- **사례와 농담의 경계가 애매할 때:** 그 얘기가 개념 이해에 기여하면 살리고, 분위기 환기용이면 뺀다.

### 2. 깊이 — 독학자료 표준

- **수업을 듣지 않은 독자가 이 글만 읽고 개념을 이해할 수 있어야 한다.** 정리·요약이 아니라 자체 학습이 가능한 텍스트가 목표다.
- 단순 요약 금지. **개념의 배경·메커니즘·그림·예시·시사점**까지 펼친다.
- 강의에서 잠깐 언급한 인물(예: Stein, Roy, Halbert White)도 **누구이고 왜 중요한지** 한두 줄 설명한다.
- 같은 개념의 여러 형태 (예: Sharpe ratio = 1차/2차 모먼트 비율)를 **다른 시각으로 묶어** 보여준다.
- 강의에서 제시된 **숫자(샘플 사이즈, 비율, TMU 같은 단위)는 정확히** 적는다.
- 강의 마지막에 **"## 부록 — 오늘의 메타 메시지"** 박스로 그 회차의 큰 그림을 압축한다.

#### 2-1. 섹션당 서술 밀도 기준 — 반드시 지킬 것

**각 `## N.` 섹션은 본문 산문이 최소 150자 이상이어야 한다.** 표·수식·bullet만으로 채운 섹션은 미완성으로 간주한다. 섹션이 짧아진다면 섹션 수를 줄이고 합쳐서라도 각 섹션의 밀도를 높여야 한다.

**직관 단락(intuition paragraph)을 모든 핵심 개념에 포함한다.** 아래 패턴을 따른다:

```
## N. 개념 이름

[개념이 등장한 배경 · 어떤 문제를 해결하는지 — 1~2 문장]

[메커니즘 · 직관 설명 — 산문으로 충분히 펼치기]

**직관:** [한 문장으로 핵심을 잡는 비유 또는 평어 설명]

[수식이 있다면 → 유도 과정 또는 "왜 이 식인지" 한 줄 이상]

[실생활 응용 예시 — 구체적이고 기억에 남는 것]
```

수식을 쓸 때는 반드시 그 앞이나 뒤에 "이 식이 말하는 것은 …", "분자가 …이고 분모가 …인 이유는 …" 식의 언어 설명을 붙인다. 수식만 달랑 쓰는 것은 금지한다.

### 3. 주제 먼저, 표·개념 목록은 나중에 — 독학자료의 핵심 원칙

**모든 표, 비교, 개념 나열, 분류 박스 앞에는 그 주제 자체에 대한 본문 설명이 반드시 선행되어야 한다.** 표는 이미 이해한 내용을 정리하는 도구이지, 개념을 처음 가르치는 도구가 아니다.

#### 3-1. 표 최소주의 — 표를 산문으로 쓸 수 있다면 산문이 낫다

표는 **두 개 이상의 대상을 여러 기준으로 동시에 비교**할 때만 사용한다. 그 외에는 산문으로 쓴다.

❌ 나쁜 예 (설명을 표로 압축):

```
| 요인 | 방향 |
|------|------|
| Salience | 높을수록 ↑ |
| Effort | 높을수록 ↓ |
```

→ 독자는 왜 Salience가 높으면 어텐션이 올라가는지, Effort가 왜 음수인지를 표만 봐서는 알 수 없다.

✅ 좋은 예 (산문 먼저 → 표는 정리용):

```
Salience(현저성)는 자극의 물리적 두드러짐이다. 배경과 크게 다른 색깔, 갑작스러운
움직임처럼 자극 자체의 속성에 의해 의식의 관여 없이 자동으로 어텐션을 포획한다.
반대로 Effort는 그 자극을 인식하기 위해 필요한 노력을 뜻한다. 보기 어려운 위치에
있는 정보는 어텐션이 덜 가게 되므로, SEEV 수식에서 음수(−) 부호를 갖는다.

이 두 요인이 어떻게 작용하는지 정리하면 다음과 같다:

| 요인 | 방향 | 성질 |
```

**표를 여러 개 연속으로 쓰는 것은 원칙적으로 금지다.** 표 사이에는 반드시 설명 산문이 들어가야 한다.

각 섹션은 다음 순서를 따른다:

1. **이 개념이 무엇인가** — 한 문장 정의
2. **왜 등장했는가** — 어떤 문제를 해결하기 위해, 어떤 맥락에서
3. **어떻게 작동하는가** — 메커니즘, 직관, 수식, 구체적 예시
4. **그 다음에** 표·분류·비교·하위 정리 등 시각 도구 사용

❌ 나쁜 예 (배경 설명 없이 바로 표):

```
### Lasso vs Ridge
| 항목 | Lasso | Ridge |
| 패널티 | L1 | L2 |
| 변수 선택 | 가능 | 불가능 |
```

→ 독자는 "Lasso가 뭔지", "왜 비교하는지" 모른 채 표를 봐야 한다.

✅ 좋은 예 (주제 설명 → 표):

```
### Lasso (L1 Regularization)

회귀분석에서 변수가 너무 많으면 과적합이 발생한다. Lasso는 이를
해결하기 위해 1996년 Robert Tibshirani가 제안한 기법으로,
회귀계수의 절댓값 합에 패널티를 부여하여 일부 계수를 정확히 0으로
만들어 변수를 자동 선택한다...

[정의 → 직관 → 메커니즘 → 예시 충분히 설명]

이러한 Lasso의 특성은 Ridge와 비교하면 더 명확해진다:

| 항목 | Lasso | Ridge |
| ... | ... | ... |
```

**핵심:** "표가 등장하기 전, 독자가 이미 그 표에 나오는 모든 용어를 자신의 언어로 설명할 수 있어야 한다."

### 4. 직관 우선, 수식 보조

- 직관적·시각적·기하학적 설명을 선호한다.
- 수식 앞뒤로 "이게 왜 이렇게 되는지"를 풀어서 설명한다.
- 핵심 메커니즘이나 직관은 반드시 명시한다 (결과만 적지 말고 이유까지).
- 추상적 정의보다 구체적 예시로 먼저 잡고 일반화로 넘어가는 흐름을 선호한다.

#### 4-1. "직관:" 레이블 적극 사용

개념 설명 뒤, 수식 뒤, 또는 메커니즘 설명 뒤에 **"직관:" 레이블을 붙인 한두 문장**을 달아 독자가 머릿속에 그림을 그릴 수 있게 한다.

```
직관: 강의실 전체의 평균 키를 구하려면, 남학생·여학생을 따로 평균 낸 뒤
인원 비율로 가중하면 된다. LIE는 이 당연한 원리를 일반화한 것이다.
```

이 레이블이 없으면 독자는 수식의 "의미"를 스스로 해석해야 하므로 독학이 어려워진다.

#### 4-2. 응용 예시는 구체적이고 기억에 남게

"예를 들어 A가 B이다"처럼 추상적인 예시는 쓰지 않는다. 독자가 읽고 나서 친구에게 설명할 수 있을 정도로 생생한 예시를 쓴다.

❌ 추상적: "예를 들어 확률 변수가 큰 값을 가질 때 Markov 부등식을 적용하면…"

✅ 구체적: "평균 소득이 100만 원인 집단에서 1,000만 원 이상인 사람의 비율은 최대 10%이다. 이것이 Markov 부등식이 말하는 전부다."

응용이 여러 개라면 `**응용 1 —**`, `**응용 2 —**` 형식으로 명시적으로 구분한다.

### 5. 인용문은 꼭 필요할 때만

- 교수님 인용문(`>` 블록)은 **남발하지 않는다.**
- 다음 경우에만 인용한다:
  - 그 말 자체가 핵심 메시지를 가장 잘 전달할 때
  - 교수님 특유의 표현이 학습 포인트를 살릴 때
  - 직접 인용해야 의미가 살 때 (자기고백·실명 사례 등)
- 그 외에는 내용을 자기 말로 풀어 정리한다. 인용 블록을 장식처럼 쓰지 않는다.

### 6. 문체 — 본문은 격식체, 인용·구어체 예시만 예외

- **본문 설명은 "~이다.", "~한다." 문어체 격식체로 작성한다.** ("~합니다"체 아님, "~해/야/지" 톤도 아님)
  - ❌ "Lasso는 변수 선택이 가능해."
  - ❌ "Lasso는 변수 선택이 가능합니다."
  - ✅ "Lasso는 변수 선택이 가능하다."
- **예외 1:** 교수님 인용문(`>` 블록) — 원문 구어체 그대로 살린다.
- **예외 2:** 구어체로 설명해야 직관이 살아나는 짧은 예시·비유 — 인용 부호 안에 담거나 자연스럽게 삽입.
- 단답형 결론 금지. 왜 그런지 풀어 서술한다.

### 7. 시각적 도구 — 표준 패턴

- **표(table):** 두 개 이상 대상을 여러 기준으로 동시 비교할 때만 — **산문으로 쓸 수 있으면 산문이 낫다.** 반드시 본문 설명 뒤에.
- **`<div class="boxed">`:** 핵심 공식·결론·정의 강조 (회차당 4~10개)
- **`<div class="keypoint">`:** 시험 포인트, 핵심 직관, "착각하기 쉬운 부분" (노란 박스, 회차당 3~7개)
- **`<div class="part-header">제 N부 — 주제</div>`:** 큰 묶음 (회차당 보통 6~11부)
- **`## 1. 섹션`:** 부 안의 섹션 (전체 **20~35개** 권장 — 섹션 수보다 각 섹션의 밀도가 중요하다)
- **`### 소섹션`:** 섹션 안의 세부 항목 (응용, 사례, 유도 등을 분리할 때)
- **`---`:** 큰 섹션 사이 구분선

**섹션 수 가이드라인 변경 이유:** 30~40개를 채우려다 보면 섹션당 산문이 짧아지고 표로 채우는 경향이 생긴다. 20~35개 범위에서 각 섹션이 충분히 풍부하게 쓰이는 것이 우선이다.

### 8. 강의자료 페이지 참조 표기 — 슬라이드와 함께 보기 위한 연결고리

정리본은 독학자료로 독립 사용하는 동시에, 원본 강의 슬라이드를 열어 놓고 함께 볼 때도 유용해야 한다. 이를 위해 **두 가지 페이지 참조 주석**을 모든 독학정리본에 반드시 포함한다.

#### 8-1. 섹션 제목 페이지 범위 주석

모든 `## N.` 섹션 제목 끝에 해당 강의자료(슬라이드)의 페이지 범위를 기재한다.

**형식:**
```
## N. 섹션 제목 *(강의자료명, pp.X-Y)*
```

**예시:**
```markdown
## 3. No-Overlap 시스템: 순차 작업의 구조 *(M3.2, pp.20-23)*
## 14. Fruit Snack 문제 설정 — Work Elements와 Precedence *(M3.3, pp.35-38)*
## 8. DHM의 정의와 역사 *(M3.3.1, p.11)*
## 9. DHM 연구 사례 1 *(DHM 논문1 참고자료)*
## 2. 시험 안내와 기말고사 범위 *(수업 공지)*
```

**표기 규칙:**
- 강의자료명은 파일명 앞부분 그대로 사용 (M3.1.1, M3.2, M3.3 Fordism 부록 등)
- 논문·참고자료는 "AR 논문", "DHM 논문1", "KLM-GOMS 논문" 등 약칭 허용
- 페이지가 단일 페이지면 `p.X`, 범위면 `pp.X-Y`
- 수업 공지·시험 안내만 담긴 섹션은 `*(수업 공지)*`
- 여러 자료를 걸치는 경우: `*(M3.2, pp.107-110; M3.3, pp.1-3)*`

**페이지 매핑 방법:**
- 강의 준비 단계에서 `pdftotext`로 각 PDF를 추출해 페이지별 첫 줄을 파악 후 섹션 내용과 매칭
- 수업범위 파일(예: `526수업범위.txt`)이 있으면 우선 참고

---

#### 8-2. 그림·표 원본 페이지 주석 (인라인)

강의 슬라이드의 특정 그림이나 표를 **함께 봐야 이해가 깊어지는 문단이나 표 바로 다음 줄**에 인라인 주석을 삽입한다.

**형식:**
```
*(→ [그림/표 간략 설명]: [자료명], [페이지] 그림/표 참고)*
```

**예시:**
```markdown
*(→ Before FD 동선도 / Before FPC 시퀀스: M3.1.2, p.16-17 그림 참고)*
*(→ Fruit Snack Work Element 표 + Precedence 다이어그램: M3.3, p.35-36 그림 참고)*
*(→ MTM-1 Data Card (거리×케이스별 TMU 조회표): M3.1.3 참고2 표 참고)*
*(→ Travel Time + Adjustment Time 교차 최적점 그래프: M3.2, pp.100-105 그림 참고)*
*(→ 9개 부서 배치 단계별 다이어그램: M3.4 CORELAP, pp.6-20 그림 참고)*
```

**삽입 기준 — 아래에 해당하면 반드시 삽입:**

| 상황 | 이유 |
|------|------|
| Before/After 다이어그램·FD 동선도·FPC 시퀀스가 있는 경우 | 공간 구조는 그림 없이 설명 불가 |
| 수치 계산 예시 표가 슬라이드에 별도 존재 (공식 + 숫자 예시) | 검산·확인에 원본 필요 |
| 슬라이드에만 있는 실물 사진·실험 결과 그래프 | 텍스트로 복원 불가 |
| 복잡한 다단계 알고리즘 예시 (CRAFT Cost Matrix, CORELAP 배치 그리드 등) | 단계별 그림 없이 이해 어려움 |
| 데이터 조회표 (MTM-1 Data Card, SAE 레벨 구분표, AEIOUX 관계 행렬 등) | 실제 값을 참조해야 계산 가능 |
| Before/After 성능 비교 화면 (드론 Display, 자동차 시트 컨트롤 등) | 시각적 대비 없이 설명이 추상적 |

**삽입 불필요 — 생략:**
- 정리본의 산문이나 표로 원본 내용이 충분히 재현된 경우
- 슬라이드가 텍스트 bullet만으로 구성된 경우
- 섹션 제목의 `*(자료명, pp.X-Y)*`로 이미 충분히 안내된 경우

**삽입 위치:**
- 해당 표나 다이어그램을 설명하는 문단 **바로 다음 줄** (별도 줄, 들여쓰기 없음)
- 표·코드블록·수식 블록의 **닫는 태그(`</div>`, 마지막 표 행) 바로 다음 줄**

---

### 9. 마크다운 작성 규칙

- **파일명:** `수업이름_몇월몇일_독학정리본` 형식을 반드시 따른다.
  - ✅ `과학적관리_5월12일_독학정리본.md` → `과학적관리_5월12일_독학정리본.pdf`
  - ✅ `경제통계학_3월30일_독학정리본.md` → `경제통계학_3월30일_독학정리본.pdf`
  - ❌ `과관_5월12일_강의정리.md` (과목 약칭 + "강의정리" 형식 사용 금지)
  - ❌ `경제통계학_4월6일_강의정리_v2.md` (`_v2` 같은 버전 접미사 금지)
- **문서 제목:** `# [과목명] 독학용 정리본 — [날짜]`
  - ✅ `# 과학적관리 독학용 정리본 — 5월 12일`
  - ✅ `# 경제통계학 독학용 정리본 — 3월 30일`
- 부제: 첫 줄 다음에 `> [날짜] — [강의 주제 압축]`
- 부 구분: `<div class="part-header">제 N부 — 주제</div>`
- 큰 섹션: `## 1. 섹션 제목` (전체 통틀어 연속 번호)
- 소섹션: `### 부분 제목` (번호 없음)
- 수식: `$$...$$` (디스플레이) 또는 `$...$` (인라인). LaTeX 문법.
- **수식 안에 한글 X.** 한글 들어가야 하면 `\text{한글}` 사용:
  - ❌ `$위험 = \sigma$`
  - ✅ `$\text{위험} = \sigma$`

---

## 독학자료 구조 템플릿 (전형적 흐름)

긴 강의(50~100분) 회차 기준:

```
# 과목명 독학용 정리본 — 날짜
> 날짜 — 그 회차의 핵심 주제들 한 줄

<div class="part-header">제 1부 — 도입 / 배경 지식</div>
## 1. 직전 시간 내용 *(강의자료명, pp.X-Y)*
## 2. 오늘 다룰 큰 그림 *(강의자료명, pp.X-Y)*

<div class="part-header">제 2부 — 첫 번째 큰 주제</div>
## 3. [주제 X는 무엇인가] *(강의자료명, pp.X-Y)*

...개념 설명 산문...

*(→ [그림/표 설명]: 자료명, p.X 그림/표 참고)*   ← 슬라이드 그림/표가 있을 때만

## 4. [메커니즘·예시·직관] *(강의자료명, pp.X-Y)*
## 5. [분류·비교] *(강의자료명, pp.X-Y)*

(중략)

<div class="part-header">제 N부 — (선택) 수업 운영 / 과제 안내</div>
## XX. 시험·과제·발표 일정 *(수업 공지)*

<div class="part-header">제 마지막부 — 종합</div>
## 마지막. 한 줄 정리

## 부록 — 오늘의 메타 메시지
<div class="boxed">
오늘 배운 것 한 줄로...
</div>
```

**주의:** "지난 시간 복습"이라는 표현보다는 "배경 지식" 또는 "전제 개념"으로 프레이밍하는 편이 독학자료에 더 적합하다. 독자가 지난 시간 수업을 듣지 않았을 수도 있기 때문이다.

---

## 클로바노트 텍스트 처리 팁

음성 인식 텍스트는 다음 패턴이 흔해:

- **전문 용어 오타:** 발음 비슷한 일반 단어로 잘못 인식 (예: "타입" → "타임", "표본" → "표면")
- 영어 전문용어 한글 인식: "샘플", "베리언스" 등은 영어로 복원 (Variance 등) 또는 한글+영어 병기
- **반복·말 더듬:** "그 그 그러니까" → "그러니까". 깔끔하게 정리.
- **구어 → 문어:** 말로 한 표현을 글로 자연스럽게. 단, 교수님 톤은 살리되 정리.
- **수치 인식 오류:** "이백오십이"가 "이병오시벼" 식으로 깨질 수 있음. 문맥(예: 1년 거래일)으로 252 같은 정확한 숫자 복원.

---

## 사용자가 자주 하는 요청

- "이거 강의 내용이야. 정리해줘" → 정리 + PDF 둘 다 (독학자료 깊이)
- "정리한 거 PDF로 만들어줘" → 변환만
- "더 깊이 구체화해줘" → 이미 깊이가 있으면 그 위에 배경·예시·시각화를 더 풀어쓰기
- "이 부분 직관 빠진 것 같은데 다시 정리해줘" → 마크다운 수정 후 재변환
- "두 강의 합쳐서 한 PDF로" → 마크다운 합친 후 변환
- "원본은 그대로 두고" → 사용자가 별도 지시할 경우에만 suffix 사용 (기본은 접미사 없음)

---

## 변환 명령어

마크다운 파일이 준비되면 — **둘 중 환경에 맞는 것 하나**를 쓴다(둘 다 같은 `template.html`로 동일한 A4 PDF를 만든다).

**(A) Node가 설치된 PC — 정석 경로:**
```bash
./make-pdf.sh 강의노트.md 강의노트.pdf      # 옵션: --keep-html (중간 HTML 보존)
```

**(B) Node가 없는 PC — 파이썬 대체 경로 (이 시스템 폴더 동봉):**
```bash
py md2pdf_nonode.py 강의노트.md 강의노트.pdf
```
- 사전 1회: `py -m pip install --user markdown`
- 수식은 MathJax CDN으로 렌더하므로 변환 시 인터넷 연결 필요. Chrome/Edge는 자동 탐지.
- 두 경로 모두 결과 PDF는 지정한 위치에 생성된다.

---

## 처음 한 번만: 셋업

**(A) Node 경로를 쓸 때** — `./setup.sh` 실행. Node 의존성(`katex`, `marked`)을 설치한다. (이 시스템 폴더엔 `node_modules`가 이미 동봉돼 있어 보통 생략 가능. 깨졌으면 재설치.)

**(B) 파이썬 경로를 쓸 때** — `py -m pip install --user markdown` 한 번. Node 불필요.

> 참고: 이 작업을 한 PC에는 Node가 설치돼 있지 않아 (B) 파이썬 경로를 기본으로 쓴다. 다른 PC에서 Node가 있으면 (A)가 더 정석이다.

**PDF 변환에는 Chrome 또는 Chromium-based 브라우저가 필요해:**
- Windows: Chrome 또는 Edge가 기본 위치에 설치돼 있으면 자동 탐지
- Mac: Chrome 또는 Edge 설치
- Linux: `chromium`, `chromium-browser`, `google-chrome` 명령어 중 하나

스크립트가 자동으로 탐지하니까 별도 설정 불필요. **wkhtmltopdf는 더 이상 사용하지 않음** (오래된 QtWebKit 기반이라 KaTeX 분수 막대 등이 깨짐).

---

## 문제 해결

- **"node: command not found"** → Node.js 설치 필요. https://nodejs.org/
- **"Chrome/Chromium/Edge 중 어느 것도 못 찾았어"** → Chrome 설치 필요
- **수식이 빨간 글씨로 "수식 오류"** → 수식 안에 한글이 들어있는지 확인. `\text{}` 사용
- **한글이 안 보임** → 시스템에 한글 폰트(Noto Sans CJK KR 등) 설치 확인
- **node_modules 깨짐 (Google Drive 동기화 이슈)** → 로컬 디렉토리에 복사 후 npm install 다시

---

## 회고 — 이 가이드의 출처

이 가이드는 2026년 1학기 경제통계학·과학적관리·기타 과목들의 정리를 통해 다듬어진 결과물이다. 처음에는 v1/v2 버전 구분이 있었으나, 독학자료 하나의 표준으로 통합되었다. 버전 구분은 더 이상 없다.

핵심 원칙은 다음 일곱 가지이다:

1. **수업을 듣지 않은 독자도 이 파일만으로 이해 가능해야 한다.**
2. **표·개념 목록 앞에는 반드시 주제 자체에 대한 본문 설명이 선행되어야 한다.**
3. **본문은 "~이다." 격식체로 작성하되, 인용과 구어체 예시는 예외로 허용한다.**
4. **섹션당 산문 밀도를 높인다 — 표로 압축하지 말고, 직관 단락을 반드시 포함한다.**
5. **섹션 수보다 각 섹션의 깊이가 우선이다 — 20~35개 범위에서 충분히 풍부하게.**
6. **모든 `## N.` 섹션 제목 끝에 강의자료 페이지 범위를 표기한다** — `*(자료명, pp.X-Y)*` 형식. 슬라이드를 열어서 함께 확인할 수 있도록.
7. **슬라이드의 특정 그림·표·다이어그램을 봐야 하는 문단 다음에는 인라인 주석을 삽입한다** — `*(→ 설명: 자료명, p.X 그림/표 참고)*` 형식. Before/After 동선도, 수치 계산 예시표, 알고리즘 그리드, 실물 사진, 데이터 조회표가 대표적 대상.

**문체 기준 모델 파일:** `예시/문체기준_경제통계학_3월30일.md` (이 시스템 폴더에 동봉)
이 파일의 서술 밀도, 직관 단락 스타일, 응용 예시 수준이 앞으로 모든 독학자료의 기준이다. 새 정리본을 쓸 때 이 파일을 참고 기준으로 삼는다. 완성본 전체 예시는 `예시/완성예시_경제통계학_6월8일.md` 참고.

**파일명 기준:** `과목명_M월D일_독학정리본.md` / `.pdf` (예: `경제통계학_6월8일_독학정리본.md`). 파일명 날짜는 공백 없이(`6월8일`), 문서 제목 날짜는 공백 포함(`# … — 6월 8일`). 과목 약칭(`과관`)·`_v2` 접미사·`강의정리` 표기는 쓰지 않는다.

**페이지 참조 주석(§8) 적용 기준:** 슬라이드가 `M3.1`처럼 모듈·페이지 구조가 뚜렷한 과목(예: 과학적관리)에는 `*(자료명, pp.X-Y)*`를 넣는다. 강의노트가 한 권으로 길게 이어지고 수업범위 페이지가 불명확한 과목(예: 경제통계학)에는 생략한다 — 부정확한 페이지를 넣느니 빼는 편이 낫다.
"""

with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("Gemini API 키", type="password", help="비우면 .env의 키 사용")
    quality_mode = st.checkbox("🔁 품질 검증 모드", help="정리 → 3중 병렬 평가 → 미달이면 자동 재작성 (느리지만 정확)")
    with st.expander("📝 노션에도 저장"):
        save_notion = st.checkbox("노션에 저장")
        notion_token = st.text_input("Notion 토큰", type="password", help="비우면 .env 사용")
        notion_page = st.text_input("Notion 페이지 ID / URL", help="비우면 .env 사용")

with st.expander("① 정리 가이드 (펼쳐서 수정 · 기본 = 내 가이드)", expanded=False):
    guide = st.text_area("정리 가이드", DEFAULT_GUIDE, height=320, label_visibility="collapsed")

st.markdown("**② 강의 자료 — 파일 업로드(.txt/.md/.pdf, 여러 개 OK) 또는 붙여넣기**")
files = st.file_uploader("강의 파일", type=["txt", "md", "pdf"], accept_multiple_files=True)
pasted = st.text_area("또는 여기에 붙여넣기", height=180, placeholder="클로바노트 텍스트...")


def extract_text(f):
    if f.name.lower().endswith(".pdf"):                       # PDF면 텍스트 추출
        reader = PdfReader(f)
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    raw = f.read()                                            # txt/md면 그냥 읽기
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp949", errors="ignore")           # 한글 인코딩 안전망


def md_to_notion_blocks(md):
    """마크다운 → 노션 블록 (제목/불릿/콜아웃/볼드, HTML태그 제거)"""
    def rich(s):
        s = re.sub(r"<[^>]+>", "", s)[:1900]                  # HTML 태그 제거 + 길이 제한
        out = []
        for i, seg in enumerate(re.split(r"\*\*(.+?)\*\*", s)):
            if seg:
                out.append({"type": "text", "text": {"content": seg}, "annotations": {"bold": i % 2 == 1}})
        return out or [{"type": "text", "text": {"content": s}}]

    blocks = []
    for line in md.split("\n"):
        s = line.strip()
        if not s:
            continue
        if s.startswith("### "):
            blocks.append({"object": "block", "type": "heading_3", "heading_3": {"rich_text": rich(s[4:])}})
        elif s.startswith("## "):
            blocks.append({"object": "block", "type": "heading_2", "heading_2": {"rich_text": rich(s[3:])}})
        elif s.startswith("# "):
            blocks.append({"object": "block", "type": "heading_1", "heading_1": {"rich_text": rich(s[2:])}})
        elif s.startswith("💡"):
            blocks.append({"object": "block", "type": "callout", "callout": {"rich_text": rich(s[1:].strip()), "icon": {"emoji": "💡"}}})
        elif s.startswith("> "):
            blocks.append({"object": "block", "type": "quote", "quote": {"rich_text": rich(s[2:])}})
        elif s.startswith(("- ", "* ")):
            blocks.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": rich(s[2:])}})
        elif s in ("---", "***"):
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        else:
            blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": rich(s)}})
    return blocks


def gemini_text(client, system, user):
    """Gemini 1회 호출: system(역할) + user(입력) → 텍스트"""
    r = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user,
        config=types.GenerateContentConfig(system_instruction=system),
    )
    return r.text


def quality_loop(client, lecture, guide, status):
    """오케스트레이션: 정리 → 3중 병렬 평가 → 미달이면 재작성 (최대 2회)"""
    import concurrent.futures as cf

    status.write("✍️ 작성자: 초안 작성 중...")
    summary = gemini_text(client, guide, f"다음 강의 자료를 정리해줘:\n\n{lecture}")

    # 3개 평가자 — 역할(system) + 입력 구성(lambda)
    evals = {
        "완전성": ("너는 '완전성' 검사관이다. [강의 녹음]의 내용이 [정리본]에 빠짐없이 담겼는지 검사한다. "
                "누락된 중요 개념·예시·수치를 모두 찾아라. 사소한 군더더기는 무시한다. "
                "첫 줄에 PASS(누락 없음) 또는 FAIL(누락 있음)만 쓰고, 다음 줄부터 누락 목록을 적어라.",
                lambda s: f"[강의 녹음]\n{lecture}\n\n[정리본]\n{s}"),
        "정확성": ("너는 '정확성' 검사관이다. [정리본]이 [강의 녹음]에 없는 내용을 지어내거나 사실을 왜곡했는지 검사한다. "
                "첫 줄에 PASS 또는 FAIL만 쓰고, 다음 줄부터 문제 목록을 적어라.",
                lambda s: f"[강의 녹음]\n{lecture}\n\n[정리본]\n{s}"),
        "가이드": ("너는 '가이드 준수' 검사관이다. [정리본]이 [정리 가이드] 규칙(직관 단락, 표 앞 설명, 격식체 등)을 지켰는지 검사한다. "
                "첫 줄에 PASS 또는 FAIL만 쓰고, 다음 줄부터 위반 목록을 적어라.",
                lambda s: f"[정리 가이드]\n{guide}\n\n[정리본]\n{s}"),
    }

    for rnd in range(2):  # 최대 2회 재작성
        status.write(f"🔎 평가 라운드 {rnd + 1}: 3개 검사관 병렬 실행...")
        with cf.ThreadPoolExecutor(max_workers=3) as ex:
            futs = {name: ex.submit(gemini_text, client, sysmsg, mk(summary))
                    for name, (sysmsg, mk) in evals.items()}
            results = {}
            for name, f in futs.items():
                try:
                    results[name] = f.result()
                except Exception:
                    results[name] = "PASS\n(평가 호출 실패 — 건너뜀)"

        fails = {}
        for name, text in results.items():
            passed = "PASS" in text.strip().split("\n")[0].upper()
            status.write(f"   · {name}: {'✅ 통과' if passed else '❌ 미달'}")
            if not passed:
                fails[name] = text

        if not fails:
            status.write("🎉 전부 통과 — 완료")
            return summary

        status.write("🛠️ 수정자: 피드백 반영해 재작성 중...")
        feedback = "\n\n".join(f"[{n} 검사관]\n{t}" for n, t in fails.items())
        summary = gemini_text(
            client, guide,
            "아래 [정리본]을 [피드백]에 따라 개선하라. 누락은 추가, 왜곡은 수정, 가이드 위반은 교정한다. "
            "[강의 녹음] 원문을 참고해 정확히 보강하라.\n\n"
            f"[강의 녹음]\n{lecture}\n\n[정리본]\n{summary}\n\n[피드백]\n{feedback}"
        )

    status.write("⚠️ 최대 횟수 도달 — 마지막 버전 사용")
    return summary


parts = []
for f in (files or []):
    parts.append(f"### [{f.name}]\n{extract_text(f)}")        # 파일명도 같이
if pasted.strip():
    parts.append(pasted)
lecture = "\n\n".join(parts)                                  # 모든 자료 합치기

if st.button("정리하기", type="primary"):
    if not lecture.strip():
        st.warning("강의 자료를 올리거나 붙여넣어줘.")
    else:
        try:
            client = genai.Client(api_key=api_key) if api_key.strip() else genai.Client()
            if quality_mode:
                with st.status("🔁 품질 검증 루프 (정리→평가→재작성)...", expanded=True) as status:
                    summary = quality_loop(client, lecture, guide, status)
            else:
                with st.spinner("제미나이가 정리하는 중... (길면 1~2분)"):
                    resp = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=f"다음 강의 자료를 정리해줘:\n\n{lecture}",
                        config=types.GenerateContentConfig(system_instruction=guide),
                    )
                    summary = resp.text
            st.success("완료!")
            # AI 결과를 격리된 iframe에 렌더 → AI가 뱉은 HTML/CSS가 페이지 스크롤을 못 건드림
            _body = mdlib.markdown(summary, extensions=["tables", "fenced_code", "sane_lists"])
            components.html(
                """<style>
                  .doc{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;line-height:1.7;color:#1a1a1a;font-size:15px;padding:6px 12px}
                  .doc h1{font-size:1.7em;border-bottom:2px solid #eee;padding-bottom:.2em}
                  .doc h2{font-size:1.35em;margin-top:1.4em;border-bottom:1px solid #eee;padding-bottom:.15em}
                  .doc h3{font-size:1.12em;margin-top:1.1em}
                  .doc table{border-collapse:collapse;margin:1em 0}
                  .doc th,.doc td{border:1px solid #ddd;padding:6px 10px;text-align:left}
                  .doc th{background:#f5f7fa}
                  .doc blockquote{border-left:3px solid #c7d2fe;margin:1em 0;padding:.3em 1em;color:#444;background:#f8faff}
                  .doc code{background:#f2f2f2;padding:.1em .3em;border-radius:4px}
                  .doc pre{background:#f7f7f7;padding:10px;border-radius:6px;overflow:auto}
                  .doc hr{border:none;border-top:1px solid #eee;margin:1.4em 0}
                </style>
                <div class="doc">""" + _body + "</div>",
                height=680, scrolling=True,
            )
            st.download_button("📥 .md 다운로드", summary, file_name="강의정리.md")

            with st.spinner("PDF 만드는 중... (수식 렌더링, 길면 30초)"):
                try:                                          # 네 md2pdf + template.html 재사용
                    tmp_md = os.path.join(tempfile.gettempdir(), "summary_in.md")
                    tmp_pdf = os.path.join(tempfile.gettempdir(), "summary_out.pdf")
                    with open(tmp_md, "w", encoding="utf-8") as fh:
                        fh.write(summary)
                    md2pdf_nonode.convert(tmp_md, tmp_pdf)
                    with open(tmp_pdf, "rb") as fh:
                        st.download_button("📄 PDF 다운로드", fh.read(),
                                           file_name="강의정리.pdf", mime="application/pdf")
                except Exception as pe:
                    st.warning(f"PDF 생성 실패: {pe}  (Chrome/markdown 설치 확인. .md는 위에서 받기 가능)")

            if save_notion:                                   # '노션에 저장' 체크됐으면
                tok = notion_token.strip() or os.environ.get("NOTION_TOKEN")
                pid_raw = notion_page.strip() or os.environ.get("NOTION_PARENT_PAGE_ID") or ""
                m = re.search(r"[0-9a-fA-F]{32}", pid_raw.replace("-", ""))   # URL/대시 형태도 자동으로 ID만 추출
                pid = m.group(0) if m else pid_raw
                if not tok or not pid:
                    st.warning("노션 토큰/페이지 ID가 없어. .env에 넣거나 위 '노션에도 저장' 칸에 입력해줘.")
                else:
                    notion = Client(auth=tok)
                    blocks = md_to_notion_blocks(summary)
                    title = next((l.strip()[2:] for l in summary.split("\n")
                                  if l.strip().startswith("# ")), "강의 정리")[:100]
                    page = notion.pages.create(
                        parent={"page_id": pid},
                        properties={"title": {"title": [{"text": {"content": title}}]}},
                        children=blocks[:100],
                    )
                    for i in range(100, len(blocks), 100):    # 노션 100블록 제한 대응
                        notion.blocks.children.append(block_id=page["id"], children=blocks[i:i + 100])
                    st.success("노션에도 저장됨!")
                    st.markdown(f"[👉 노션에서 보기]({page['url']})")
        except Exception as e:
            st.error(f"에러: {e}\n\nGemini API 키(.env 또는 위 칸)를 확인해줘.")
