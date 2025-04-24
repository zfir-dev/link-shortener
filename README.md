# Link Shortener

A Flask-based link shortener application.

## Prerequisites

- Docker
- Docker Compose

## Configuration

Create a `.env` file in the root directory with the following variables:

```env
FLASK_SECRET_KEY=your_secret_key
ADMIN_PASSWORD=your_admin_password
TWOFACTOR_SECRET_KEY=your_2fa_secret
DATABASE_HOST=your_db_host
DATABASE_NAME=your_db_name
DATABASE_USER=your_db_user
DATABASE_PORT=your_db_port
DATABASE_PASSWORD=your_db_password
RECORDS_PER_PAGE=3
```

## Running the Application

### Production Mode (Default)

The application runs in production mode by default. To run it:

1. Clone the repository:
```bash
git clone <repository-url>
cd link-shortener
```

2. Build the application:
```bash
docker build -t link-shortener .
```

3. Access the application at `http://localhost:5000`

### Development Mode

To run the application in development mode with hot-reloading and debug features:

1. Start the application:
```bash
docker-compose up
```

3. Access the application at `http://localhost:5000`

4. Stop the application:
```bash
docker-compose down
```
