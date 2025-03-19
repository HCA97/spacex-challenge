FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["gunicorn", "-w", "1", "--threads", "30", "-b", "0.0.0.0:8000", "app:app"]
