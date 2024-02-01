FROM python:3.9-windowsservercore-ltsc2019
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app/
EXPOSE 5000
ENV FLASK_ENV=production
CMD ["python", "app.py"]
