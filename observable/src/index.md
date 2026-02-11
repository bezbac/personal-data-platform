```js
import * as Plot from "npm:@observablehq/plot";

const top100 = [...await FileAttachment("assets/lastfm_artists_with_most_listening_weeks.parquet").parquet()].slice(0, 100)
```

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
