-- asset.name = lastfm_scrobbles_with_ranking
-- asset.description = All lastfm scrobbles with personal song popularity ranking
-- asset.depends = lastfm_scrobbles

WITH song_totals AS (
    SELECT
        name AS track_name,
        artist_name,
        COUNT(*) AS total_plays
    FROM
        {{ ref("lastfm_scrobbles") }}
    GROUP BY 1, 2
),

ranked_songs AS (
    SELECT
        track_name,
        artist_name,
        total_plays,
        DENSE_RANK() OVER (ORDER BY total_plays DESC) AS rank
    FROM
        song_totals
)

SELECT
    s.timestamp,
    s.name AS track_name,
    s.artist_name,
    r.rank,
    r.total_plays
FROM
    {{ ref("lastfm_scrobbles") }} AS s
    INNER JOIN
        ranked_songs AS r
        ON
            s.name = r.track_name
            AND s.artist_name = r.artist_name
ORDER BY
    1 ASC
