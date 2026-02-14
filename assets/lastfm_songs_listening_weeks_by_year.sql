-- asset.name = lastfm_songs_listening_weeks_by_year
-- asset.description = Group songs by the number of unique weeks they were listened to, broken down by year
-- asset.depends = lastfm_scrobbles

SELECT
    name AS track_name,
    artist_name,
    YEAR(DATE_TRUNC('week', timestamp)) AS year,
    COUNT(DISTINCT DATE_TRUNC('week', timestamp)) AS listening_weeks
FROM
    {{ ref("lastfm_scrobbles") }}
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3
