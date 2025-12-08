FROM python:3.11-slim-bookworm

# Создаём непривилегированного пользователя для безопасности и прав доступа
RUN useradd -m -u 1001 appuser
USER appuser

WORKDIR /app

# Минимальные зависимости (убрали дубликаты, которые вызывали exit code 100)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    unzip \
    libnss3 \
    libgbm1 \
    libasound2 \
    libatspi2.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Chrome 143 (устанавливаем в /app/chrome, чтобы избежать прав root)
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

# Python-зависимости (как appuser)
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Код приложения
COPY --chown=appuser:appuser . /app

# Папки для undetected-chromedriver (чтобы не было Permission denied /app/.local)
ENV UC_DRIVER_CACHE_DIR=/app/.uc_cache
ENV XDG_CACHE_HOME=/app/.cache
RUN mkdir -p /app/.uc_cache /app/.cache && chown -R appuser:appuser /app/.uc*

# Для Railway
ENV PYTHONUNBUFFERED=1

CMD ["python3", "main.py"]