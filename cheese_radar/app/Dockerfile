FROM python:3.11-slim-bookworm

WORKDIR /app

# 1. Системные пакеты
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget unzip libnss3 libgbm1 libasound2 libatspi2.0-0 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# 2. Chrome 143 + chromedriver 143
RUN wget -q https://storage.googleapis.com/chrome-for-testing-public/143.0.7499.40/linux64/chrome-linux64.zip \
    && unzip chrome-linux64.zip && mv chrome-linux64 /opt/chrome \
    && ln -sf /opt/chrome/chrome /usr/bin/google-chrome \
    && chmod +x /opt/chrome/chrome && rm -rf chrome-linux64*

RUN wget -q https://storage.googleapis.com/chrome-for-testing-public/143.0.7499.40/linux64/chromedriver-linux64.zip \
    && unzip chromedriver-linux64.zip \
    && mv chromedriver-linux64/chromedriver /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver && rm -rf chromedriver-linux64*

# 3. Python-пакеты глобально
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Код
COPY . /app

ENV HOME=/tmp
ENV XDG_CACHE_HOME=/tmp/.cache
ENV UC_DRIVER_CACHE_DIR=/tmp/uc_cache
ENV TEMP=/tmp
ENV TMP=/tmp
ENV TMPDIR=/tmp

# Дополнительно — на всякий случай создаём папки (они в /tmp, там всегда права есть)
RUN mkdir -p /tmp/.cache /tmp/uc_cache

ENV PYTHONUNBUFFERED=1

CMD ["python3", "main.py"]