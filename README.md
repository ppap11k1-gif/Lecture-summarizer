# 📚 강의 자동 정리기 (Gemini)

강의 자료(클로바노트 텍스트 · `.txt` · `.md` · 슬라이드 `.pdf`)를 넣으면
내 정리 가이드대로 **자동 요약 → 품질 검증(3중 평가) → 재작성**하고,
결과를 **화면 · Markdown · PDF · Notion**으로 내보내는 **로컬 웹 도구**.

> 이 폴더 전체가 "하나의 프로그램"이다. 실행은 `run.bat` 하나면 끝.

---

## 빠른 시작 (3단계)

1. **Python 설치** (https://python.org) — 이미 있으면 생략
2. 이 폴더에서 터미널 열고:
   ```
   pip install -r requirements.txt
   ```
3. **Gemini API 키** 발급 (https://aistudio.google.com → Get API key, 무료·카드 X)

## 키 넣기 (둘 중 하나)

- **(a) 파일로:** `.env.example`를 복사해 `.env`로 만들고 키를 채운다.
  ```
  GEMINI_API_KEY=...           (필수)
  NOTION_TOKEN=...             (노션 저장 쓸 때만)
  NOTION_PARENT_PAGE_ID=...    (노션 저장 쓸 때만 · URL 통째로 넣어도 됨)
  ```
- **(b) 앱에서:** 사이드바의 키 칸에 직접 입력.

## 실행

- **`run.bat` 더블클릭** (또는 터미널: `streamlit run app.py`)
- 브라우저가 열리면:
  - **(사이드바) 설정** — Gemini 키 / 🔁 품질 검증 모드 / 📝 노션 저장
  - **① 정리 가이드** — 기본 = 내 가이드 (펼쳐서 수정 가능)
  - **② 강의 자료** 업로드(.txt/.md/.pdf, 여러 개 OK) 또는 붙여넣기 → **정리하기**
  - 결과: 화면 + 📥 `.md` + 📄 `PDF` (+ 노션 페이지)

## 🔁 품질 검증 모드 (선택)

켜면: **작성 → 3개 검사관 병렬 평가(완전성·정확성·가이드준수) → 미달이면 자동 재작성**(최대 2회).
- 더 정확하지만 호출이 늘어 느려짐. (Gemini 무료라 비용은 0)

---

## 필요한 것
- Python · 인터넷 · **Chrome**(PDF 출력용) · Gemini API 키(무료)

## 파일 설명
| 파일 | 역할 |
|---|---|
| `app.py` | 프로그램 본체 |
| `template.html` | PDF 스타일(템플릿) |
| `md2pdf_nonode.py` | PDF 변환기 (Chrome 사용) |
| `requirements.txt` | 필요한 라이브러리 목록 |
| `run.bat` | 실행 버튼 |
| `.env` | 내 API 키 (**남한테 공유 X**) |
| `.env.example` | 키 양식 (이걸 복사해서 .env 만들기) |

## 끄기
- 검은 창(서버)에서 **Ctrl+C** 또는 그 창 닫기.

## 트러블슈팅
- `No module named ...` → `pip install -r requirements.txt` 다시
- PDF 생성 실패 → Chrome 설치 확인 / `pip install markdown`
- 노션 저장 안 됨 → 토큰·페이지ID 확인 + 그 노션 페이지에 통합(Connections) 연결했는지 확인
- 키 에러(401) → `.env`의 키에 따옴표·공백·`...` 없는지 확인
