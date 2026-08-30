from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = "kiwi-secret"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "KhizarIlyas2008!",
    "database": "kiwi"
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

@app.route("/")
def home():
    return redirect(url_for("songs"))

# View all songs
@app.route("/songs")
def songs():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM Songs ORDER BY id DESC")
    songs = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("songs.html", songs=songs)

# Add a new song
@app.route("/songs/add", methods=["GET", "POST"])
def add_song():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        artist = request.form.get("artist", "").strip()
        url = request.form.get("url", "").strip()

        if not name or not artist or not url:
            flash("All fields are required.")
            return redirect(url_for("add_song"))

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO Songs (name, artist, url) VALUES (%s, %s, %s)",
            (name, artist, url)
        )

        conn.commit()
        cur.close()
        conn.close()

        flash("Song added successfully!")
        return redirect(url_for("songs"))

    return render_template("add_song.html")

@app.route("/songs/delete/<int:song_id>", methods=["POST"])
def delete_song(song_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM Songs WHERE id = %s", (song_id,))
    conn.commit()

    cur.close()
    conn.close()

    flash("Song deleted successfully!")
    return redirect(url_for("songs"))
if __name__ == "__main__":

    app.run(debug=True, port=5002)

