FROM python:3
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8082
COPY . .
CMD [ "gunicorn", "--bind", "0.0.0.0:8082", "main:app" ]
