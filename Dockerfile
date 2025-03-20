# Используем официальный образ Python 3.11 (slim для уменьшения размера)
FROM python:3.11-slim

# Устанавливаем пользователя root для установки зависимостей
USER root

# Устанавливаем зависимости для работы с SQLite и Google Sheets (если нужны системные библиотеки)
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv build-essential python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Создаём директорию /app и устанавливаем её как рабочую
RUN mkdir -p /app
WORKDIR /app

# Копируем весь проект в контейнер
COPY . /app

# Устанавливаем переменную окружения для файла учетных данных Google Sheets
ENV GOOGLE_CREDENTIALS_PATH="/app/stemsmanagerbot-3b6400c7024.json"

# Меняем владельца, чтобы пользователь appuser мог записывать в /app
RUN useradd -m appuser && \
    chown -R appuser:appuser /app

# Переключаемся на пользователя appuser для безопасности
USER appuser

# Создаём и активируем виртуальное окружение, устанавливаем зависимости
RUN python3 -m venv /app/venv && \
    /app/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Указываем команду для запуска бота
CMD ["/app/venv/bin/python", "main.py"]
