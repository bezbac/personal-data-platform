```js
import * as Plot from "npm:@observablehq/plot";
import * as d3 from "npm:d3";

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
    <h2>Song Rank Timeline</h2>
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

This visualization shows the evolution of song rankings over time based on
Last.FM scrobble data. Each point represents a scrobble, positioned by its
timestamp and colored/shaded by its rank (where rank 1 is the most-played song).
