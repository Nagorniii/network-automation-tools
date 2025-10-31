FROM python:3.11-slim-bullseye

# Оновлення пакетів і установка ping/netcat
RUN apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends iputils-ping netcat && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копіюємо requirements.txt та ставимо залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо код проекту
COPY app/ .

CMD ["python", "main.py"]
