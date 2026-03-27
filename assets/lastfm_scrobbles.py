# asset.name = lastfm_scrobbles
# asset.description = Raw data for Lastfm scrobbles

import json
import os

import polars as pl

from utils import extract_featured_artists


def lastfm_scrobbles() -> pl.DataFrame:
    path = os.path.join(os.getcwd(), "input/lastfm", "scrobbles.json")

    # The json file is an array of arrays of objects
    # The code reads the file in python, deserializes the json,
    # and then converts it to a polars dataframe
    with open(path) as f:
        data = f.read()
        data = json.loads(data)

    flattened = [item for sublist in data for item in sublist]
    df = pl.DataFrame(flattened)

    # The artist column is a dictionary
    # - The key "#text" contains the artist name
    # - The key "mbid" contains the artist's MusicBrainz ID.
    df = df.with_columns(
        pl
        .col("artist")
        .map_elements(lambda x: x["#text"] if isinstance(x, dict) else None)
        .alias("artist_name"),
        pl
        .col("artist")
        .map_elements(lambda x: x["mbid"] if isinstance(x, dict) else None)
        .alias("artist_mbid"),
    )
    df = df.drop("artist")

    # The album column is a dictionary
    # - The key "#text" contains the album name
    # - The key "mbid" contains the album's MusicBrainz ID.
    df = df.with_columns(
        pl
        .col("album")
        .map_elements(lambda x: x["#text"] if isinstance(x, dict) else None)
        .alias("album_name"),
        pl
        .col("album")
        .map_elements(lambda x: x["mbid"] if isinstance(x, dict) else None)
        .alias("album_mbid"),
    )
    df = df.drop("album")

    # Get the timestamp column and convert it to a datetime
    df = df.with_columns(
        pl
        .col("date")
        .map_elements(lambda x: x["uts"] if isinstance(x, dict) else None)
        .cast(pl.Int64)
        # Convert from seconds to milliseconds and then to a datetime
        .map_elements(lambda x: x * 1000 if x is not None else None)
        .cast(pl.Datetime(time_unit="ms"))
        .alias("timestamp")
    )
    df = df.drop("date")

    # Extract featured artists from track names
    # Handles patterns like (feat. Artist), [feat. Artist], (with Artist), etc.
    # See extract_featured_artists() docstring for full details
    df = df.with_columns(
        pl
        .col("name")
        .map_elements(extract_featured_artists, return_dtype=pl.List(pl.String))
        .alias("featured_artists")
    )

    # Drop columns that are not needed for analysis
    df = df.drop("streamable")
    df = df.drop("image")

    return df
