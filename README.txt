강의 자동 정리기 (Gemini 버전)
=====================================

[처음 1회 준비]
1. Python 설치 (python.org) — 이미 있으면 생략
2. 이 폴더에서 터미널 열고 (또는 아래 '실행' 참고):
      pip install -r requirements.txt
3. AI Studio(https://aistudio.google.com)에서 Gemini API 키 발급 (무료, 카드 X)
4. 키 넣기 — 둘 중 하나:
   (a) 이 폴더의 .env 파일 열어 GEMINI_API_KEY= 뒤에 키 붙여넣기, 또는
   (b) 앱 화면의 'Gemini API 키' 칸에 직접 입력

[실행]
- run.bat 더블클릭   (또는 터미널에서: streamlit run app.py)
- 브라우저가 열리면:
    ① 정리 가이드 확인/수정 (원하면 내 CLAUDE.md 붙여넣기)
    ② 강의 파일 업로드(.txt/.md/.pdf, 여러 개 가능) 또는 붙여넣기
    ③ '정리하기' 클릭 → 요약 표시 + .md 다운로드

[끄기]
- 검은 창에서 Ctrl+C, 또는 그 창 닫기

[참고]
- PDF는 '텍스트'만 추출됨 (슬라이드 그림/도표는 안 들어감)
- 각자 자기 Gemini 키로 사용 = 각자 무료 한도 사용
