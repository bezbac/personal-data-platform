-- asset.name = spotify_listening_time_by_day
-- asset.description = Spotify listening time by day
-- asset.depends = spotify_track_plays

SELECT
    DATE_TRUNC('day', end_time) AS day,
    SUM(ms_played) AS ms_played
FROM
    {{ ref("spotify_track_plays") }}
GROUP BY 1
ORDER BY 1
