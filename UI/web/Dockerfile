FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY UI/index.html ./index.html
COPY UI/css ./css
COPY UI/js ./js
COPY UI/web/start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 8080
CMD ["sh", "/app/start.sh"]
