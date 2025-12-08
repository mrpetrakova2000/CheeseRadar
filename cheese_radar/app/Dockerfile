FROM python:3.11-slim-bookworm

WORKDIR /app

# Всё делаем от root — на Railway это нормально и работает
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget unzip libnss3 libgbm1 libasound2 libatspi2.0-0 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Chrome 143
RUN wget -q https://storage.googleapis.com/chrome-for-testing-public/143.0.7499.40/linux64/chrome-linux64.zip \
    && unzip chrome-linux64.zip \
    && mv chrome-linux64 /opt/chrome \
    && ln -sf /opt/chrome/chrome /usr/bin/google-chrome \
    && chmod +x /opt/chrome/chrome \
    && rm -rf chrome-linux64*

# Chromedriver 143
RUN wget -q https://storage.googleapis.com/chrome-for-testing-public/143.0.7499.40/linux64/chromedriver-linux64.zip \
    && unzip chromedriver-linux64.zip \
    && mv chromedriver-linux64/chromedriver /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver \
    && rm -rf chromedriver-linux64*

# Устанавливаем Python-пакеты глобально (никакого --user!)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . /app

# Эти три переменные — всё, что нужно для undetected-chromedriver
ENV HOME=/app
ENV XDG_CACHE_HOME=/app/.cache
ENV UC_DRIVER_CACHE_DIR=/app/.uc_cache

ENV PYTHONUNBUFFERED=1

CMD ["python3", "main.py"]