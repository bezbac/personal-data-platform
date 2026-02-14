```js
import * as Plot from "npm:@observablehq/plot";
import * as d3 from "npm:d3";

const truncate = (str, maxLength) =>
  str.length > maxLength ? str.slice(0, maxLength - 3) + "..." : str;

const artistsData = [
  ...(await FileAttachment(
    "assets/lastfm_artists_with_most_listening_weeks.parquet",
  ).parquet()),
]
  .slice(0, 100)
  .map((d) => ({
    ...d,
    display_name: d.artist_name,
    listening_weeks: Number(d.listening_weeks),
  }));

const albumsData = [
  ...(await FileAttachment(
    "assets/lastfm_albums_with_most_listening_weeks.parquet",
  ).parquet()),
]
  .slice(0, 100)
  .map((d) => ({
    ...d,
    display_name: `${truncate(d.album_name, 25)} - ${truncate(
      d.artist_name,
      20,
    )}`,
    listening_weeks: Number(d.listening_weeks),
  }));

const songsData = [
  ...(await FileAttachment(
    "assets/lastfm_songs_with_most_listening_weeks.parquet",
  ).parquet()),
]
  .slice(0, 100)
  .map((d) => ({
    ...d,
    display_name: `${truncate(d.track_name, 25)} - ${truncate(
      d.artist_name,
      20,
    )}`,
    listening_weeks: Number(d.listening_weeks),
  }));

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

```js
const viewTypeInput = Inputs.radio(["Artists", "Albums", "Songs"], {
  value: "Artists",
  label: "",
});
const viewType = Generators.input(viewTypeInput);
```

```js
const currentData = (() => {
  switch (viewType) {
    case "Artists":
      return artistsData;
    case "Albums":
      return albumsData;
    case "Songs":
      return songsData;
    default:
      return artistsData;
  }
})();
```

<div class="card">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
        <h2 style="margin: 0;">${viewType} by count of weeks with at least one play</h2>
        ${viewTypeInput}
    </div>
    ${resize((width) => Plot.plot({
        width,
        marginLeft: viewType === "Artists" ? 120 : 200,
        marginRight: 40,
        x: { label: "Listening weeks" },
        y: { label: null },
        marks: [
            Plot.barX(currentData, {
                x: "listening_weeks",
                y: "display_name",
                sort: { y: "-x" },
                fill: "grey"
            }),
            Plot.text(currentData, {
                x: "listening_weeks",
                y: "display_name",
                text: (d) => d.listening_weeks,
                dx: 12,
                anchor: "start"
            }),
            Plot.ruleX([0])
        ]
    }))}
</div>
