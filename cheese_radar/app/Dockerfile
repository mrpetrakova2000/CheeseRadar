FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    gnupg \
    unzip \                     # ← добавили
    libnss3 \
    libatk-bridge2.0-0 \
    libxkbcommon0 \
    libgbm1 \
    libasound2 \
    libatspi2.0-0 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q https://storage.googleapis.com/chrome-for-testing-public/143.0.7499.40/linux64/chrome-linux64.zip \
    && unzip chrome-linux64.zip \
    && mv chrome-linux64 /opt/google-chrome \
    && ln -sf /opt/google-chrome/chrome /usr/bin/google-chrome \
    && chmod +x /opt/google-chrome/chrome \
    && rm chrome-linux64.zip

# 3. Качаем chromedriver той же версии
RUN wget -q https://storage.googleapis.com/chrome-for-testing-public/143.0.7499.40/linux64/chromedriver-linux64.zip \
    && unzip chromedriver-linux64.zip \
    && mv chromedriver-linux64/chromedriver /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver \
    && rm -rf chromedriver-linux64.zip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Код приложения
COPY . /app

ENV PYTHONUNBUFFERED=1

CMD ["python3", "main.py"]