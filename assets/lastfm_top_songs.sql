-- asset.name = lastfm_top_songs
-- asset.description = Most scrobbled songs on last.fm
-- asset.depends = lastfm_scrobbles

SELECT
    name AS track_name,
    artist_name,
    COUNT(*) AS scrobbles
FROM
    {{ ref("lastfm_scrobbles") }}
GROUP BY 1, 2
ORDER BY 3 DESC
