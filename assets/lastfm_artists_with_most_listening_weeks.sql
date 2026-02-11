-- asset.name = lastfm_artists_with_most_listening_weeks
-- asset.description = Group artists by the number of unique weeks they were listened to
-- asset.depends = lastfm_scrobbles

SELECT
    artist_name,
    COUNT(DISTINCT DATE_TRUNC('week', timestamp)) AS listening_weeks
FROM
    {{ ref("lastfm_scrobbles") }}
GROUP BY 1
ORDER BY 2 DESC
