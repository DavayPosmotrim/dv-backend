# Создать образ на основе базового слоя,
# который содержит файлы ОС и интерпретатор Python 3.10.
FROM python:3.10-slim

# Установить нужные пакеты для поддержки локалей
RUN apt-get update && apt-get install -y locales

# Сгенерировать нужную локаль
RUN sed -i '/ru_RU.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

# Установить переменные окружения для локали
ENV LANG ru_RU.UTF-8
ENV LANGUAGE ru_RU:ru
ENV LC_ALL ru_RU.UTF-8

# Переходим в образе в директорию /app: в ней будем хранить код проекта.
# Если директории с указанным именем нет, она будет создана. 
# Название директории может быть любым.
WORKDIR /app
# Дальнейшие инструкции будут выполняться в директории /app

# Скопировать с локального компьютера файл зависимостей
# в текущую директорию (текущая директория — это /app).
COPY requirements.txt .

# Выполнить в текущей директории команду терминала
# для установки зависимостей.
RUN pip install -r requirements.txt --no-cache-dir
RUN pip install daphne supervisor

# Скопировать всё необходимое содержимое 
# той директории локального компьютера, где сохранён Dockerfile,
# в текущую рабочую директорию образа — /app.
COPY . .

# Create log directory
RUN mkdir -p /app/logs

# Copy Supervisor configuration
COPY supervisord.conf /etc/supervisord.conf

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run Supervisor when the container launches
CMD ["supervisord", "-c", "/etc/supervisord.conf"]
