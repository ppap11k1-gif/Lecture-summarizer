# Hugging Face Spaces (Docker) — Chrome 포함 → 클라우드에서 PDF 생성 가능
FROM python:3.11-slim

# Chromium(=Chrome) + 한글 폰트(PDF용) 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium fonts-nanum \
    && rm -rf /var/lib/apt/lists/*
ENV CHROME_BIN=/usr/bin/chromium

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# HF Spaces는 비루트(user 1000)로 실행 → 권한 처리
RUN useradd -m -u 1000 user && chown -R user /app
USER user
ENV HOME=/home/user

EXPOSE 7860
CMD ["streamlit", "run", "app.py", \
     "--server.port=7860", "--server.address=0.0.0.0", "--server.headless=true"]
