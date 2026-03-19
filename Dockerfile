FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:$PORT"]
