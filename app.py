from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    make_response,
    send_from_directory,
)
import os
from psycopg2 import pool
import shortuuid
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__, static_folder="static")

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


from datetime import datetime


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


def is_valid_passcode(passcode):
    correct_passcode = os.environ.get("AUTH_PASSCODE")
    return passcode == correct_passcode


@app.route("/validate-passcode", methods=["POST"])
def validate_passcode():
    passcode = request.json.get("passcode")

    if is_valid_passcode(passcode):
        response = make_response(
            jsonify({"message": "Passcode validated successfully"}), 200
        )
        response.set_cookie("passcode", passcode)
        return response
    else:
        return jsonify({"error": "Incorrect passcode"}), 401


@app.route("/")
def index():
    passcode = request.cookies.get("passcode")
    if passcode == os.environ.get("AUTH_PASSCODE"):
        try:
            page = request.args.get("page", default=1, type=int)

            conn = get_db_connection()
            with conn.cursor() as cur:
                offset = (page - 1) * records_per_page
                cur.execute(
                    "SELECT * FROM links ORDER BY updated_at DESC LIMIT %s OFFSET %s",
                    (records_per_page, offset),
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
                    records_per_page=records_per_page,
                )
        except Exception as e:
            if conn:
                release_db_connection(conn)

            return render_template(
                "index.html",
                links=[],
                total_records=0,
                page=1,
                records_per_page=records_per_page,
            )

    return render_template("password.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.environ.get("PORT", 3000))
