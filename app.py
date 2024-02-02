from flask import Flask, request, jsonify, render_template, make_response, send_from_directory
import os
import psycopg2
import shortuuid
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static')

conn = psycopg2.connect(
    host=os.environ.get("DATABASE_HOST"),
    database=os.environ.get("DATABASE_NAME"),
    user=os.environ.get("DATABASE_USER"),
    password=os.environ.get("DATABASE_PASSWORD"),
    sslmode='require'
)

@app.route('/fetch-metadata', methods=['POST'])
def fetch_metadata():
    url = request.json.get('url')
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        og_title = soup.find('meta', property='og:title')['content']
        og_description = soup.find('meta', property='og:description')['content']
        og_image = soup.find('meta', property='og:image')['content']
        return jsonify({'ogTitle': og_title, 'ogDescription': og_description, 'ogImage': og_image})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/shorten', methods=['POST'])
def shorten_url():
    url = request.json.get('url')
    og_title = request.json.get('ogTitle')
    og_description = request.json.get('ogDescription')
    og_image = request.json.get('ogImage')
    short_id = shortuuid.ShortUUID().random(length=7)
    try:
        with conn.cursor() as cur:
            cur.execute('INSERT INTO links (short_id, original_url, og_title, og_description, og_image) VALUES (%s, %s, %s, %s, %s) RETURNING *',
                        (short_id, url, og_title, og_description, og_image))
            conn.commit()
            return jsonify({'shortId': short_id, 'originalUrl': url, 'ogTitle': og_title, 'ogDescription': og_description, 'ogImage': og_image})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/<short_id>', methods=['GET'])
def redirect_short_url(short_id):
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT original_url, og_title, og_description, og_image FROM links WHERE short_id = %s", (short_id,))
            result = cur.fetchone()
            if result is None:
                return 'Shortened URL not found', 404

            original_url, og_title, og_description, og_image = result

            cur.execute("UPDATE links SET clicks = clicks + 1 WHERE short_id = %s", (short_id,))
            conn.commit()

            html_response = f"""
                <html>
                    <head>
                        <title>{og_title or 'Redirect'}</title>
                        <!-- Twitter Card metadata -->
                        <meta name="twitter:card" content="summary" />
                        <meta name="twitter:site" content="@nytimesbits" />
                        <meta name="twitter:creator" content="@nickbilton" />
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
                            }}, 5000);
                        </script>
                    </body>
                </html>
            """

            return html_response
    except Exception as e:
        return str(e), 500

@app.route('/delete/<short_id>', methods=['DELETE'])
def delete_short_url(short_id):
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM links WHERE short_id = %s RETURNING *", (short_id,))
            deleted_row = cur.fetchone()
            conn.commit()
            if deleted_row is None:
                return jsonify({'error': 'Shortened URL not found'}), 404
            return jsonify({'message': 'URL deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/robots.txt')
def serve_robots_txt():
    return send_from_directory(app.static_folder, 'robots.txt')

def is_valid_passcode(passcode):
    correct_passcode = os.environ.get("AUTH_PASSCODE")
    return passcode == correct_passcode

@app.route('/validate-passcode', methods=['POST'])
def validate_passcode():
    passcode = request.json.get('passcode')

    if is_valid_passcode(passcode):
        response = make_response(jsonify({'message': 'Passcode validated successfully'}), 200)
        response.set_cookie('passcode', passcode)
        return response
    else:
        return jsonify({'error': 'Incorrect passcode'}), 401

@app.route('/')
def index():
    passcode = request.cookies.get('passcode')
    if passcode == os.environ.get("AUTH_PASSCODE"):
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM links")
                links = cur.fetchall()
                return render_template('index.html', links=links)
        except Exception as e:
            print(e)
            return render_template('index.html', links=[])

    return render_template('password.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get("PORT", 3000))

