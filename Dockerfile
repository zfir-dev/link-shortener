FROM python:3.9
WORKDIR .
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
ENV FLASK_ENV=production
CMD ["waitress-serve", "--port=5000", "app:app"]
