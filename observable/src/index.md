```js
import * as Plot from "npm:@observablehq/plot";
import * as d3 from "npm:d3";

const top100 = [
  ...(await FileAttachment(
    "assets/lastfm_artists_with_most_listening_weeks.parquet",
  ).parquet()),
].slice(0, 100);
const scrobbles = [
  ...(await FileAttachment(
    "assets/lastfm_scrobbles_with_ranking.parquet",
  ).parquet()),
].map((d) => ({
  ...d,
  rank: Number(d.rank),
  total_plays: Number(d.total_plays),
}));

const maxRank = Math.max(...scrobbles.map((d) => d.rank));
const colorScale = d3
  .scaleSequential()
  .domain([1, maxRank])
  .interpolator(d3.interpolateBlues);
```

<div class="card">
    <h2>Last.fm Scrobbles by Rank</h2>
    ${resize((width) => Plot.plot({
        width,
        height: 400,
        marginLeft: 60,
        x: { label: "Time", type: "time" },
        y: { 
            label: "Song Rank (by total plays)",
            domain: [maxRank + 1, 0]
        },
        color: {
            type: "sequential",
            domain: [1, maxRank],
            scheme: "blues"
        },
        marks: [
            Plot.dot(scrobbles, {
                x: "timestamp",
                y: "rank",
                fill: "rank",
                r: 1,
                opacity: 0.6
            }),
            Plot.ruleY([0], { stroke: "#ccc" })
        ]
    }))}
</div>

<div class="card">
    <h2>Artists by count of weeks with at least one play</h2>
    ${resize((width) => Plot.plot({
        width,
        marginLeft: 120,
        x: { label: "Listening weeks" },
        y: { label: null },
        marks: [
            Plot.barX(top100, {
                x: "listening_weeks",
                y: "artist_name",
                sort: { y: "-x" },
                fill: "grey"
            }),
            Plot.text(top100, {
                x: "listening_weeks",
                y: "artist_name",
                text: (d) => d.listening_weeks,
                dx: 12,
                anchor: "start"
            }),
            Plot.ruleX([0])
        ]
    }))}
</div>
