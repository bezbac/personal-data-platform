# asset.name = spotify_track_plays
# asset.description = Raw data for Spotify track plays

import glob
import os

import polars as pl


def spotify_track_plays() -> pl.DataFrame:
    file_pattern = os.path.join(
        os.getcwd(), "input/spotify", "StreamingHistory_music_*.json"
    )
    files = glob.glob(file_pattern)

    data_frames = []
    for file in files:
        df = pl.read_json(file)
        data_frames.append(df)

    df = pl.concat(
        data_frames,
    )

    # Rename all columns to snake_case
    df = df.rename({
        "endTime": "end_time",
        "artistName": "artist_name",
        "trackName": "track_name",
        "msPlayed": "ms_played",
    })

    # Set correct data types
    df = df.with_columns(
        pl.col("end_time").str.strptime(pl.Datetime, format="%Y-%m-%d %H:%M"),
        pl.col("artist_name").cast(pl.Utf8),
        pl.col("track_name").cast(pl.Utf8),
        pl.col("ms_played").cast(pl.Int64),
    )

    return df
