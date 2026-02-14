import os
import asyncio
import pandas as pd

from sanic import Sanic
from sanic.response import json
from sanic_ext import Extend
from sanic_cors import CORS
from dotenv import load_dotenv

load_dotenv()

from tsne import increment_with_tsne_data
from tfidf import calculate_correlation_matrix

app = Sanic("tcc_api")
#app.config.CORS_ORIGINS = "*"
#Extend(app)

CORS(app, resources={
    r"/*": {
        "origins": ["https://vispot-front.vercel.app"]
    }
})

MOCK_FOLDER = "mocks"
MOCK_FILES = {
    "emo": "emo_genre_dataset.csv",
    "country":"country_genre_dataset.csv",
    "hip_hop": "hip_hop_genre_dataset.csv",
    "pop": "pop_genre_dataset.csv",
    "reggae": "reggae_genre_dataset.csv",
    "rock": "rock_genre_dataset.csv",
}


def load_mock_playlists(playlists):
    tracks = []
    current_id = 1

    for playlist in playlists:
        playlist = playlist.lower()

        if playlist not in MOCK_FILES:
            continue

        file_path = os.path.join(MOCK_FOLDER, MOCK_FILES[playlist])

        if not os.path.exists(file_path):
            continue

        df = pd.read_csv(file_path)

        for _, row in df.iterrows():
            track = {
                "id": current_id,
                "name": row.get("name", ""),
                "artist": row.get("artists_name", ""),
                "playlist": playlist,
                "lyrics": row.get("lyrics", ""),

                # Audio features used by TSNE
                "duration_ms": row.get("duration_ms", 0),
                "danceability": row.get("danceability", 0),
                "energy": row.get("energy", 0),
                "loudness": row.get("loudness", 0),
                "speechiness": row.get("speechiness", 0),
                "acousticness": row.get("acousticness", 0),
                "instrumentalness": row.get("instrumentalness", 0),
                "liveness": row.get("liveness", 0),
                "valence": row.get("valence", 0),
                "tempo": row.get("tempo", 0),
            }

            tracks.append(track)
            current_id += 1

    return tracks


@app.get("/mock")
async def mock_playlist(request):
    playlists = request.args.getlist("playlist")

    if not playlists:
        return json({"songs": [], "correlation": []})

    tracks_info = load_mock_playlists(playlists)

    if not tracks_info:
        return json({"songs": [], "correlation": []})

    loop = asyncio.get_running_loop()

    tracks_info = await loop.run_in_executor(
        None,
        increment_with_tsne_data,
        tracks_info
    )

    lyrics = [track.get("lyrics", "") for track in tracks_info]

    correlation = await loop.run_in_executor(
        None,
        calculate_correlation_matrix,
        lyrics
    )

    return json({
        "songs": tracks_info,
        "correlation": correlation
    })


@app.get("/")
async def health(_):
    return json({"status": "ok"})


#if __name__ == "__main__":
#    app.run(host="0.0.0.0", port=1337, workers=4)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000))
    )