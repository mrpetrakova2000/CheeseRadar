FROM python:3.11-slim-bookworm

# Запускаем всё от непривилегированного пользователя (важно!)
RUN useradd -m -u 1001 appuser
USER appuser

WORKDIR /app

# Системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates wget gnupg unzip \
    libnss3 libatk-bridge2.0-0 libatk1.0-0 libc6 libx11-6 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxshmfence1 \
    libasound2 libatspi2.0-0 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Chrome 143
RUN wget -q https://storage.googleapis.com/chrome-for-testing-public/143.0.7499.40/linux64/chrome-linux64.zip \
    && unzip chrome-linux64.zip \
    && mkdir -p /app/chrome \
    && mv chrome-linux64/* /app/chrome/ \
    && ln -sf /app/chrome/chrome /usr/local/bin/google-chrome \
    && chmod +x /app/chrome/chrome \
    && rm -rf chrome-linux64.zip chrome-linux64

# Chromedriver 143
RUN wget -q https://storage.googleapis.com/chrome-for-testing-public/143.0.7499.40/linux64/chromedriver-linux64.zip \
    && unzip chromedriver-linux64.zip \
    && mv chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf chromedriver-linux64.zip chromedriver-linux64

# Python-зависимости (как непривилегированный пользователь)
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Код приложения
COPY --chown=appuser:appuser . /app

# Явно говорим undetected-chromedriver куда писать свои файлы
ENV UC_DRIVER_CACHE_DIR=/app/.uc_cache
ENV XDG_CACHE_HOME=/app/.cache

# Обязательно для Railway
ENV PYTHONUNBUFFERED=1

CMD ["python3", "main.py"]