-- asset.name = lastfm_albums_with_most_listening_weeks
-- asset.description = Group albums by the number of unique weeks they were listened to
-- asset.depends = lastfm_scrobbles

SELECT
    album_name,
    artist_name,
    COUNT(DISTINCT DATE_TRUNC('week', timestamp)) AS listening_weeks
FROM
    {{ ref("lastfm_scrobbles") }}
GROUP BY 1, 2
ORDER BY 3 DESC
