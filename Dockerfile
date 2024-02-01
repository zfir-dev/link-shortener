FROM python:3.9-windowsservercore
WORKDIR .
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
ENV FLASK_ENV=production
CMD ["python", "app.py"]
