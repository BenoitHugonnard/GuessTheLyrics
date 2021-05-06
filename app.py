import yaml
from flask import Flask, render_template, request, redirect, url_for
from pathlib import Path
import subprocess
import os
from utils.song import Song
from utils.lyrics import Lyrics
from utils.settings import settings
import re
import random
import copy
import urllib.parse
import base64


app = Flask(__name__)
app._static_folder = os.path.abspath("templates/static/")

current_dir = Path(__file__).absolute().parent

current = {
    "karaoke": {},
    "classic": {},
    "ladder": {}
}


def launch_data_server(port, data_dir):
    cmd = ['python', '-m', 'ComplexHTTPServer', port]
    subprocess.Popen(cmd, cwd=str(data_dir))


@app.route("/api/generate/<game_mode>/<song_name>", methods=["GET"])
def api_generate(game_mode, song_name):
    print(f"Generating song {song_name} for {game_mode}...")
    lyrics = Lyrics(song_name)

    if game_mode == "karaoke":
        answer, raw_lyrics = lyrics.generate_break("karaoke")
        current["karaoke"][song_name] = {
            "lyrics": raw_lyrics
        }

    elif game_mode == "classic":
        song = Song(song_name)
        answer, raw_lyrics = lyrics.generate_break()
        song.export_trimmed(answer.ms)
        current["classic"][song_name] = {
            "answer": answer.generate_answer(),
            "initials": answer.generate_initials(),
            "placeholder": answer.generate_placeholder(),
            "lyrics": raw_lyrics
        }
    else:
        song = Song(song_name)
        current["ladder"][song_name] = lyrics.generate_breaks()
        for idx, val in current["ladder"][song_name].items():
            if idx == "0":
                prev_break_timestamp = 0
            else:
                prev_idx = str(int(idx) - 1)
                prev_break_idx = current["ladder"][song_name][prev_idx]["break_idx"]
                prev_break_timestamp = lyrics.lyrics[prev_break_idx - settings.BREAK_SAFETY].ms
            song.export_ladder_trimmed(idx,
                                       prev_break_timestamp,
                                       val["break_timestamp"])

    print(f"Song generated !")
    return {}


@app.route("/api/initials/<game_mode>/<song_name>", methods=["GET"])
@app.route("/api/initials/<game_mode>/<song_name>/<idx>", methods=["GET"])
def api_initials(game_mode, song_name, idx=None):
    if game_mode == "classic":
        return {"initials": current["classic"][song_name]["initials"]}
    return {"initials": current["ladder"][song_name][idx]["initials"]}


@app.route("/api/submit/<game_mode>/<song_name>", methods=["POST"])
@app.route("/api/submit/<game_mode>/<song_name>/<idx>", methods=["POST"])
def api_submit(game_mode, song_name, idx=None):
    if game_mode == "classic":
        answer = current["classic"][song_name]["answer"]
    else:
        answer = current["ladder"][song_name][idx]["answer"]

    proposition = request.form["proposition"]
    try:
        regexp = re.compile(r"\w+")
        words = regexp.findall(proposition)
        assert len(answer) == len(words)
        for i in range(len(answer)):
            assert answer[i].lower() == words[i].lower()
        result = True
    except AssertionError:
        result = False
    return {
        "status": "1" if result else "0",
        "answer": " ".join(answer),
        "proposition": proposition,
        "new_idx": int(idx) + 1 if idx else None
    }


@app.route('/api/songs', methods=['GET'])
def api_songs():
    with open(current_dir / 'data' / 'config.yaml', 'r') as f:
        songs = yaml.load(f, Loader=yaml.SafeLoader)
    songs_by_cat = {}
    for song_name, info in songs.items():
        for category in info["categories"]:
            song = {
                "display_name": f"{info['author']} - {info['title']}",
                "song_name": song_name
            }
            songs_by_cat[category] = songs_by_cat.get(category, []) + [song]

    for category in songs_by_cat:
        random_song = copy.deepcopy(random.choice(songs_by_cat[category]))
        random_song["display_name"] = "Random"
        songs_by_cat[category] = [random_song] + songs_by_cat[category]

    return songs_by_cat


@app.route('/api/songs2', methods=['GET'])
def api_songs2():
    raw_path = current_dir / 'data' / 'raw2'
    songs_by_cat = {}
    for file in raw_path.glob("**/*.mp3"):
        category = file.parent.parent.name
        author = file.parent.name
        song_name = file.stem
        full_song = f"{category}/{author}/{song_name}"
        message_bytes = full_song.encode('utf-8')
        base64_bytes = base64.b64encode(message_bytes)
        song = {
            "display_name": f"{author} - {song_name}",
            "song_name": base64_bytes.decode("utf-8")
        }
        print(base64_bytes.decode("utf-8"))
        songs_by_cat[category] = songs_by_cat.get(category, []) + [song]

    for category in songs_by_cat:
        random_song = copy.deepcopy(random.choice(songs_by_cat[category]))
        random_song["display_name"] = "Random"
        songs_by_cat[category] = [random_song] + songs_by_cat[category]

    return songs_by_cat


@app.route('/')
def home():
    return render_template('layouts/home.html',
                           host=settings.DOMAIN)


@app.route('/song/<game_mode>/<song_name>', methods=['GET'])
@app.route('/song/<game_mode>/<song_name>/<idx>', methods=['GET'])
def show_song(game_mode, song_name, idx=None):
    if game_mode not in current or song_name not in current[game_mode]:
        api_generate(game_mode, song_name)

    if game_mode == "classic":
        template = 'layouts/show_song_classic.html'
        lyrics = '\n'.join(current["classic"][song_name]["lyrics"])
        level = None
        placeholder = current["classic"][song_name]["placeholder"]
    elif game_mode == "ladder":
        if idx in current["ladder"][song_name]:
            template = 'layouts/show_song_ladder.html'
            lyrics = '\n'.join(current["ladder"][song_name][idx]["lyrics_to_show"])
            level = current["ladder"][song_name][idx]["level"]
            placeholder = current["ladder"][song_name][idx]["placeholder"]
        else:
            return redirect(url_for("home"))

    else:
        api_generate(game_mode, song_name)
        template = 'layouts/show_song_karaoke.html'
        lyrics = '\n'.join(current["karaoke"][song_name]["lyrics"])
        level, placeholder = None, None

    return render_template(template,
                           song=song_name,
                           idx=idx,
                           lyrics=lyrics,
                           level=level,
                           placeholder=placeholder,
                           host=settings.DOMAIN)


if __name__ == '__main__':
    launch_data_server('5002', current_dir / 'data')
    app.run(host='0.0.0.0')
