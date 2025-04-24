# Link Shortener

A Flask-based link shortener application.

## Prerequisites

- Docker
- Docker Compose

## Running the Application

### Production Mode (Default)

The application runs in production mode by default. To run it:

1. Clone the repository:
```bash
git clone <repository-url>
cd link-shortener
```

2. Start the application:
```bash
docker-compose up
```

3. Access the application at `http://localhost:5000`

### Development Mode

To run the application in development mode with hot-reloading and debug features:

1. Open `docker-compose.yml` and uncomment the development environment variables:
```yaml
environment:
  - FLASK_ENV=production  # Comment this line
  # - FLASK_ENV=development  # Uncomment this line
  # - FLASK_DEBUG=1  # Uncomment this line
  # - FLASK_APP=app.py  # Uncomment this line
  # - SEND_FILE_MAX_AGE_DEFAULT=0  # Uncomment this line
  # - TEMPLATES_AUTO_RELOAD=True  # Uncomment this line
```

2. Start the application:
```bash
docker-compose up
```

3. Access the application at `http://localhost:5000`

## Configuration

The application can be configured through environment variables in the `docker-compose.yml` file:

- `FLASK_ENV`: Set to `production` or `development`
- `FLASK_DEBUG`: Enable/disable debug mode
- `FLASK_APP`: Specify the main application file
- `SEND_FILE_MAX_AGE_DEFAULT`: Control static file caching
- `TEMPLATES_AUTO_RELOAD`: Enable/disable template auto-reloading

## Stopping the Application

To stop the application:

```bash
docker-compose down
```

## Troubleshooting

If you encounter any issues:

1. Make sure Docker and Docker Compose are installed and running
2. Check if port 5000 is available on your system
3. Try rebuilding the containers:
```bash
docker-compose down
docker-compose build
docker-compose up
``` 