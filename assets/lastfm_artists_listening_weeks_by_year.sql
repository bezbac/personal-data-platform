-- asset.name = lastfm_artists_listening_weeks_by_year
-- asset.description = Group artists by the number of unique weeks they were listened to, broken down by year. Includes both direct listening weeks and weeks including featured appearances.
-- asset.depends = lastfm_scrobbles

WITH direct_listens AS (
    SELECT
        artist_name,
        YEAR(DATE_TRUNC('week', timestamp)) AS year,
        COUNT(DISTINCT DATE_TRUNC('week', timestamp)) AS listening_weeks
    FROM
        {{ ref("lastfm_scrobbles") }}
    GROUP BY 1, 2
),

featured_listens AS (
    SELECT
        arr AS artist_name,
        YEAR(DATE_TRUNC('week', timestamp)) AS year,
        COUNT(DISTINCT DATE_TRUNC('week', timestamp)) AS listening_weeks
    FROM
        (
            SELECT
                timestamp,
                arrayJoin(featured_artists) AS arr
            FROM
                {{ ref("lastfm_scrobbles") }}
            WHERE
                LENGTH(featured_artists) > 0
        )
    GROUP BY 1, 2
),

all_listens AS (
    SELECT * FROM direct_listens
    UNION ALL
    SELECT * FROM featured_listens
),

combined_weeks AS (
    SELECT
        artist_name,
        year,
        SUM(listening_weeks) AS listening_weeks_with_features
    FROM
        all_listens
    GROUP BY 1, 2
)

SELECT
    d.artist_name,
    d.year,
    d.listening_weeks,
    c.listening_weeks_with_features
FROM
    direct_listens AS d
    LEFT JOIN combined_weeks AS c
        ON d.artist_name = c.artist_name AND d.year = c.year
ORDER BY 1, 2
