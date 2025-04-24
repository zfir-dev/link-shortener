from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    send_from_directory,
    redirect,
    url_for,
    flash,
    session
)
import os
from psycopg2 import pool
import shortuuid
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime
import pyotp

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)
from functools import wraps

load_dotenv()

app = Flask(__name__, static_folder="static")
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "your_default_secret_key")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

users = {
    "admin": {
        "password": os.environ.get("ADMIN_PASSWORD", "adminpass"),
        "totp_secret": os.environ.get("TWOFACTOR_SECRET_KEY", pyotp.random_base32())
    }
}

class User(UserMixin):
    def __init__(self, username):
        self.id = username
        self.totp_secret = users[username]["totp_secret"]

    def __repr__(self):
        return f"<User {self.id}>"

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None

def two_factor_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not session.get("two_factor_authenticated", False):
            return redirect(url_for("two_factor"))
            
        otp_generated_at = session.get("otp_generated_at")
        current_time = datetime.now().timestamp()
        
        if not otp_generated_at or (current_time - float(otp_generated_at)) > 3600:
            logout_user()
            session.pop("two_factor_authenticated", None)
            session.pop("otp_generated_at", None)
            flash("Your session has expired. Please log in again.", "error")
            return redirect(url_for("login"))
            
        return func(*args, **kwargs)
    return decorated_view

records_per_page = int(os.environ.get("RECORDS_PER_PAGE", 10))

db_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=20,
    host=os.environ.get("DATABASE_HOST"),
    database=os.environ.get("DATABASE_NAME"),
    user=os.environ.get("DATABASE_USER"),
    password=os.environ.get("DATABASE_PASSWORD"),
    sslmode="require",
)

def get_db_connection():
    return db_pool.getconn()

def release_db_connection(conn):
    db_pool.putconn(conn)

def close_db_pool():
    db_pool.closeall()

@app.route("/fetch-metadata", methods=["POST"])
def fetch_metadata():
    url = request.json.get("url")
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        og_title = soup.find("meta", property="og:title")["content"]
        og_description = soup.find("meta", property="og:description")["content"]
        og_image = soup.find("meta", property="og:image")["content"]
        return jsonify(
            {"ogTitle": og_title, "ogDescription": og_description, "ogImage": og_image}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/shorten", methods=["POST"])
@login_required
@two_factor_required
def shorten_url():
    url = request.json.get("url")
    og_title = request.json.get("ogTitle")
    og_description = request.json.get("ogDescription")
    og_image = request.json.get("ogImage")
    short_id = shortuuid.ShortUUID().random(length=7)
    current_timestamp = datetime.now()

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO links (short_id, original_url, og_title, og_description, og_image, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *",
                (
                    short_id,
                    url,
                    og_title,
                    og_description,
                    og_image,
                    current_timestamp,
                    current_timestamp,
                ),
            )
            conn.commit()

            release_db_connection(conn)

            return jsonify(
                {
                    "shortId": short_id,
                    "originalUrl": url,
                    "ogTitle": og_title,
                    "ogDescription": og_description,
                    "ogImage": og_image,
                }
            )
    except Exception as e:
        if conn:
            release_db_connection(conn)
        return jsonify({"error": str(e)}), 500

@app.route("/<short_id>", methods=["GET"])
def redirect_short_url(short_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT original_url, og_title, og_description, og_image FROM links WHERE short_id = %s",
                (short_id,),
            )
            result = cur.fetchone()
            if result is None:
                release_db_connection(conn)

                return "Shortened URL not found", 404

            original_url, og_title, og_description, og_image = result

            current_timestamp = datetime.now()

            cur.execute(
                "UPDATE links SET clicks = clicks + 1, updated_at = %s WHERE short_id = %s",
                (current_timestamp, short_id),
            )
            conn.commit()

            html_response = f"""
                <html>
                    <head>
                        <title>{og_title or 'Redirect'}</title>
                        <!-- Twitter Card metadata -->
                        <meta name="twitter:card" content="summary" />
                        <meta name="twitter:title" content="{og_title or ''}" />
                        <meta name="twitter:description" content="{og_description or ''}" />
                        <meta name="twitter:image" content="{og_image or ''}" />
                        <!-- Open Graph (OG) metadata -->
                        <meta property="og:url" content="{original_url}" />
                        <meta property="og:title" content="{og_title or ''}" />
                        <meta property="og:description" content="{og_description or ''}" />
                        <meta property="og:image" content="{og_image or ''}" />
                    </head>
                    <body>
                        <p>Redirecting...</p>
                        <script>
                            setTimeout(function () {{
                                window.location.href = "{original_url}";
                            }}, 2000);
                        </script>
                    </body>
                </html>
            """

            release_db_connection(conn)

            return html_response
    except Exception as e:
        if conn:
            release_db_connection(conn)

        return str(e), 500

@app.route("/delete/<short_id>", methods=["DELETE"])
@login_required
@two_factor_required
def delete_short_url(short_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM links WHERE short_id = %s RETURNING *", (short_id,)
            )
            deleted_row = cur.fetchone()
            conn.commit()
            if deleted_row is None:
                release_db_connection(conn)

                return jsonify({"error": "Shortened URL not found"}), 404

            release_db_connection(conn)

            return jsonify({"message": "URL deleted successfully"}), 200
    except Exception as e:
        if conn:
            release_db_connection(conn)

        return jsonify({"error": str(e)}), 500

@app.route("/robots.txt")
def serve_robots_txt():
    return send_from_directory(app.static_folder, "robots.txt")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in users and users[username]["password"] == password:
            user = User(username)
            login_user(user)
            session["two_factor_authenticated"] = False
            session["otp_generated_at"] = datetime.now().timestamp()
            flash("Password accepted. Please enter your 2FA code.", "info")
            return redirect(url_for("two_factor"))
        else:
            flash("Invalid username or password.", "error")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.pop("two_factor_authenticated", None)
    session.pop("otp_generated_at", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/two_factor", methods=["GET", "POST"])
@login_required
def two_factor():
    if request.method == "POST":
        code = request.form.get("code")
        totp = pyotp.TOTP(current_user.totp_secret)
        
        if totp.verify(code):
            session["two_factor_authenticated"] = True
            session["otp_generated_at"] = datetime.now().timestamp()
            flash("2FA successful. You are now logged in.", "success")
            next_page = request.args.get("next") or url_for("index")
            return redirect(next_page)
        else:
            flash("Invalid 2FA code. Please try again.", "error")
    return render_template("two_factor.html")

@app.route("/")
@login_required
@two_factor_required
def index():
    try:
        page = request.args.get("page", default=1, type=int)
        conn = get_db_connection()
        with conn.cursor() as cur:
            offset = (page - 1) * records_per_page
            cur.execute(
                "SELECT * FROM links ORDER BY updated_at DESC LIMIT %s OFFSET %s",
                (records_per_page, offset)
            )
            links = cur.fetchall()
            cur.execute("SELECT COUNT(*) FROM links")
            total_records = cur.fetchone()[0]
        release_db_connection(conn)

        if not links:
            links = []
            total_records = 0
            page = 1

        return render_template(
            "index.html",
            links=links,
            total_records=total_records,
            page=page,
            records_per_page=records_per_page
        )
    except Exception as e:
        if 'conn' in locals():
            release_db_connection(conn)
        return render_template(
            "index.html",
            links=[],
            total_records=0,
            page=1,
            records_per_page=records_per_page
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.environ.get("PORT", 3000))
