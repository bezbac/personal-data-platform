# mock.output = scrobbles.json

import random
import uuid
from datetime import datetime, timedelta


def generate():
    """Generate mock Last.fm scrobble data."""
    random.seed(42)

    # Sample data for realistic mock generation
    artists = [
        ("Radiohead", "a74b1b7f-71a5-4011-9441-d0b5e4122711"),
        ("The Beatles", "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"),
        ("Pink Floyd", "83d91898-7763-47d7-b03b-b92132375c47"),
        ("Led Zeppelin", "678d88b2-87b0-403b-b63d-5da7465aecc3"),
        ("Queen", "420ca290-76c5-41af-999e-564d7c71f2a7"),
        ("Nirvana", "5b11f4ce-a62d-471e-81fc-a69a8278c7da"),
        ("The Rolling Stones", "b071f9fa-14b0-4217-8e97-eb41da73f598"),
        ("David Bowie", "5441c29d-3602-4898-b1f1-43a4d7e2b1f5"),
        ("Bob Dylan", "72c536dc-7137-4477-a521-567eeb840fa8"),
        ("Miles Davis", "561d854a-6a28-4aa7-8c99-323e6c27168e"),
        ("John Coltrane", "b625448e-bf4a-41c3-a421-72ad46cdb831"),
        ("Kendrick Lamar", "381086ea-f511-4aba-bdf9-71c753dc5077"),
        ("Kanye West", "164f0d73-1234-4e2c-8743-d77bf2191051"),
        ("Beyoncé", "859d0860-d480-4efd-970c-c05d5f1386e5"),
        ("Daft Punk", "056e4f3e-d505-4dad-8ec1-d04f521cbb56"),
        ("Aphex Twin", "f22942a1-6f70-4f02-9fbe-1cc77e7e7e7e"),
        ("Boards of Canada", "69158f97-4c07-4c4b-b71b-2221b0b9f1b5"),
        ("Massive Attack", "10adbe5e-a2c0-4bf3-8249-2b4cbf6e6e94"),
        ("Portishead", "8f6bd1e4-fbe1-4f50-aa9b-94c450ec0f11"),
        ("Radiohead", "a74b1b7f-71a5-4011-9441-d0b5e4122711"),
    ]

    albums = [
        ("OK Computer", "a1b2c3d4-e5f6-7890-abcd-ef1234567890"),
        ("Abbey Road", "b2c3d4e5-f6a7-8901-bcde-f23456789012"),
        ("The Dark Side of the Moon", "c3d4e5f6-a7b8-9012-cdef-345678901234"),
        ("Led Zeppelin IV", "d4e5f6a7-b8c9-0123-def0-456789012345"),
        ("A Night at the Opera", "e5f6a7b8-c9d0-1234-ef01-567890123456"),
        ("Nevermind", "f6a7b8c9-d0e1-2345-f012-678901234567"),
        ("Sticky Fingers", "a7b8c9d0-e1f2-3456-0123-789012345678"),
        ("The Rise and Fall of Ziggy Stardust", "b8c9d0e1-f2a3-4567-1234-890123456789"),
        ("Highway 61 Revisited", "c9d0e1f2-a3b4-5678-2345-901234567890"),
        ("Kind of Blue", "d0e1f2a3-b4c5-6789-3456-012345678901"),
        ("A Love Supreme", "e1f2a3b4-c5d6-7890-4567-123456789012"),
        ("To Pimp a Butterfly", "f2a3b4c5-d6e7-8901-5678-234567890123"),
        ("My Beautiful Dark Twisted Fantasy", "a3b4c5d6-e7f8-9012-6789-345678901234"),
        ("Lemonade", "b4c5d6e7-f8a9-0123-7890-456789012345"),
        ("Discovery", "c5d6e7f8-a9b0-1234-8901-567890123456"),
        ("Selected Ambient Works 85-92", "d6e7f8a9-b0c1-2345-9012-678901234567"),
        ("Music Has the Right to Children", "e7f8a9b0-c1d2-3456-0123-789012345678"),
        ("Mezzanine", "f8a9b0c1-d2e3-4567-1234-890123456789"),
        ("Dummy", "a9b0c1d2-e3f4-5678-2345-901234567890"),
        ("In Rainbows", "b0c1d2e3-f4a5-6789-3456-012345678901"),
    ]

    track_names = [
        "Paranoid Android",
        "Karma Police",
        "Come Together",
        "Here Comes the Sun",
        "Money",
        "Time",
        "Stairway to Heaven",
        "Black Dog",
        "Bohemian Rhapsody",
        "Don't Stop Me Now",
        "Smells Like Teen Spirit",
        "Come As You Are",
        "Paint It Black",
        "Gimme Shelter",
        "Space Oddity",
        "Heroes",
        "Like a Rolling Stone",
        "Subterranean Homesick Blues",
        "So What",
        "Blue in Green",
        "A Love Supreme Part I",
        "Naima",
        "Alright",
        "King Kunta",
        "Power",
        "Runaway",
        "Formation",
        "Single Ladies",
        "One More Time",
        "Digital Love",
        "Xtal",
        "Tha",
        "Roygbiv",
        "Music Is Math",
        "Teardrop",
        "Angel",
        "Glory Box",
        "Roads",
        "Reckoner",
        "Jigsaw Falling Into Place",
        "Weird Fishes",
    ]

    # Generate ~1000 scrobbles
    scrobbles = []
    base_time = datetime(2023, 1, 1, 12, 0, 0)

    for _ in range(1000):
        # Pick random artist, album, and track
        artist_name, artist_mbid = random.choice(artists)
        album_name, album_mbid = random.choice(albums)
        track_name = random.choice(track_names)

        # Generate a random timestamp within 2 years
        random_offset = random.randint(0, 730 * 24 * 60 * 60)
        timestamp = base_time + timedelta(seconds=random_offset)

        # Format date like Last.fm: "uts" for unix timestamp, "#text" for display
        uts = str(int(timestamp.timestamp()))
        date_text = timestamp.strftime("%d %b %Y, %H:%M")

        # Generate track MBID (or empty)
        track_mbid = str(uuid.uuid4()) if random.random() > 0.3 else ""

        artist_url_part = artist_name.replace(" ", "+")
        track_url_part = track_name.replace(" ", "+")

        # Build scrobble object matching Last.fm format
        scrobble = {
            "artist": {
                "mbid": artist_mbid,
                "#text": artist_name,
            },
            "streamable": "0",
            "image": [
                {"size": "small", "#text": "https://last.fm/fake/small.jpg"},
                {"size": "medium", "#text": "https://last.fm/fake/medium.jpg"},
                {"size": "large", "#text": "https://last.fm/fake/large.jpg"},
                {
                    "size": "extralarge",
                    "#text": "https://last.fm/fake/extralarge.jpg",
                },
            ],
            "mbid": track_mbid,
            "album": {
                "mbid": album_mbid,
                "#text": album_name,
            },
            "name": track_name,
            "url": f"https://www.last.fm/music/{artist_url_part}/_/{track_url_part}",
            "date": {
                "uts": uts,
                "#text": date_text,
            },
        }
        scrobbles.append(scrobble)

    # Sort by timestamp (newest first, like Last.fm export)
    scrobbles.sort(key=lambda x: int(x["date"]["uts"]), reverse=True)

    # Batch into sublists of 200 (like the real export format)
    batch_size = 200
    batches = [
        scrobbles[i : i + batch_size] for i in range(0, len(scrobbles), batch_size)
    ]

    return batches
