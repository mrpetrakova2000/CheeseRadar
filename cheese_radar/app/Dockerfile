FROM python:3.11-slim-bookworm

WORKDIR /app

# Один слой со всеми системными зависимостями + unzip
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    gnupg \
    unzip \
    libnss3 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxshmfence1 \
    libasound2 \
    libatspi2.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Chrome 143 (самый лёгкий и рабочий способ 2025 года)
RUN wget -q https://storage.googleapis.com/chrome-for-testing-public/143.0.7499.40/linux64/chrome-linux64.zip \
    && unzip chrome-linux64.zip \
    && mv chrome-linux64 /opt/google-chrome \
    && ln -sf /opt/google-chrome/chrome /usr/bin/google-chrome \
    && chmod +x /opt/google-chrome/chrome \
    && rm chrome-linux64.zip

# Chromedriver той же версии
RUN wget -q https://storage.googleapis.com/chrome-for-testing-public/143.0.7499.40/linux64/chromedriver-linux64.zip \
    && unzip chromedriver-linux64.zip \
    && mv chromedriver-linux64/chromedriver /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver \
    && rm -rf chromedriver-linux64.zip

# Python-зависимости и код
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV PYTHONUNBUFFERED=1

CMD ["python3", "main.py"]