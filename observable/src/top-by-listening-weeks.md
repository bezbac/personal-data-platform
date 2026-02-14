```js
import * as Plot from "npm:@observablehq/plot";

const truncate = (str, maxLength) =>
  str.length > maxLength ? str.slice(0, maxLength - 3) + "..." : str;

const artistsDataRaw = [
  ...(await FileAttachment(
    "assets/lastfm_artists_listening_weeks_by_year.parquet",
  ).parquet()),
].map((d) => ({
  ...d,
  year: Number(d.year),
  listening_weeks: Number(d.listening_weeks),
  listening_weeks_with_features: Number(d.listening_weeks_with_features),
}));

const artistsDataWithFeatures = artistsDataRaw
  .reduce((acc, d) => {
    const existing = acc.find((x) => x.artist_name === d.artist_name);
    if (existing) {
      existing.total_weeks += d.listening_weeks_with_features;
    } else {
      acc.push({
        artist_name: d.artist_name,
        display_name: d.artist_name,
        total_weeks: d.listening_weeks_with_features,
      });
    }
    return acc;
  }, [])
  .sort((a, b) => b.total_weeks - a.total_weeks)
  .slice(0, 100);

const artistsDataWithoutFeatures = artistsDataRaw
  .reduce((acc, d) => {
    const existing = acc.find((x) => x.artist_name === d.artist_name);
    if (existing) {
      existing.total_weeks += d.listening_weeks;
    } else {
      acc.push({
        artist_name: d.artist_name,
        display_name: d.artist_name,
        total_weeks: d.listening_weeks,
      });
    }
    return acc;
  }, [])
  .sort((a, b) => b.total_weeks - a.total_weeks)
  .slice(0, 100);

const albumsDataRaw = [
  ...(await FileAttachment(
    "assets/lastfm_albums_listening_weeks_by_year.parquet",
  ).parquet()),
].map((d) => ({
  ...d,
  year: Number(d.year),
  listening_weeks: Number(d.listening_weeks),
}));

const albumsData = albumsDataRaw
  .reduce((acc, d) => {
    const key = `${d.album_name}|${d.artist_name}`;
    const existing = acc.find((x) => x.key === key);
    if (existing) {
      existing.total_weeks += d.listening_weeks;
    } else {
      acc.push({
        key,
        album_name: d.album_name,
        artist_name: d.artist_name,
        display_name: `${truncate(d.album_name, 25)} - ${truncate(
          d.artist_name,
          20,
        )}`,
        total_weeks: d.listening_weeks,
      });
    }
    return acc;
  }, [])
  .sort((a, b) => b.total_weeks - a.total_weeks)
  .slice(0, 100);

const songsDataRaw = [
  ...(await FileAttachment(
    "assets/lastfm_songs_listening_weeks_by_year.parquet",
  ).parquet()),
].map((d) => ({
  ...d,
  year: Number(d.year),
  listening_weeks: Number(d.listening_weeks),
}));

const songsData = songsDataRaw
  .reduce((acc, d) => {
    const key = `${d.track_name}|${d.artist_name}`;
    const existing = acc.find((x) => x.key === key);
    if (existing) {
      existing.total_weeks += d.listening_weeks;
    } else {
      acc.push({
        key,
        track_name: d.track_name,
        artist_name: d.artist_name,
        display_name: `${truncate(d.track_name, 25)} - ${truncate(
          d.artist_name,
          20,
        )}`,
        total_weeks: d.listening_weeks,
      });
    }
    return acc;
  }, [])
  .sort((a, b) => b.total_weeks - a.total_weeks)
  .slice(0, 100);
```

```js
const viewTypeInput = Inputs.radio(["Artists", "Albums", "Songs"], {
  value: "Artists",
  label: "",
});
const viewType = Generators.input(viewTypeInput);
```

```js
const includeFeaturesInput = Inputs.radio(
  ["Include features", "Exclude features"],
  {
    value: "Include features",
    label: "",
    disabled: viewType !== "Artists",
  },
);
const includeFeatures = Generators.input(includeFeaturesInput);
```

```js
const currentData = (() => {
  switch (viewType) {
    case "Artists":
      return {
        summary:
          includeFeatures === "Include features"
            ? artistsDataWithFeatures
            : artistsDataWithoutFeatures,
        raw: artistsDataRaw,
      };
    case "Albums":
      return { summary: albumsData, raw: albumsDataRaw };
    case "Songs":
      return { summary: songsData, raw: songsDataRaw };
    default:
      return {
        summary:
          includeFeatures === "Include features"
            ? artistsDataWithFeatures
            : artistsDataWithoutFeatures,
        raw: artistsDataRaw,
      };
  }
})();
```

```js
const summaryData = currentData.summary;
const rawData = currentData.raw;

// Calculate year counts for each entity
const yearCounts = rawData.reduce((acc, d) => {
  let key;
  if (viewType === "Artists") {
    key = d.artist_name;
  } else if (viewType === "Albums") {
    key = `${d.album_name}|${d.artist_name}`;
  } else {
    key = `${d.track_name}|${d.artist_name}`;
  }
  if (!acc[key]) {
    acc[key] = new Set();
  }
  acc[key].add(d.year);
  return acc;
}, {});

// Add year count to summary data
const summaryDataWithYears = summaryData.map((d) => {
  let key;
  if (viewType === "Artists") {
    key = d.artist_name;
  } else if (viewType === "Albums") {
    key = `${d.album_name}|${d.artist_name}`;
  } else {
    key = `${d.track_name}|${d.artist_name}`;
  }
  const yearCount = yearCounts[key] ? yearCounts[key].size : 1;
  return {
    ...d,
    year_count: yearCount,
    label_text: `${d.total_weeks} week${
      d.total_weeks !== 1 ? "s" : ""
    } spanning ${yearCount} year${yearCount !== 1 ? "s" : ""}`,
  };
});

const displayNames = summaryDataWithYears.map((d) => d.display_name);

// Filter raw data to only include top 100 entities
const filteredRaw = rawData
  .filter((d) => {
    if (viewType === "Artists") {
      return summaryData.some((s) => s.artist_name === d.artist_name);
    } else if (viewType === "Albums") {
      return summaryData.some(
        (s) => s.album_name === d.album_name && s.artist_name === d.artist_name,
      );
    } else {
      return summaryData.some(
        (s) => s.track_name === d.track_name && s.artist_name === d.artist_name,
      );
    }
  })
  .map((d) => ({
    ...d,
    display_name:
      viewType === "Artists"
        ? d.artist_name
        : viewType === "Albums"
          ? `${truncate(d.album_name, 25)} - ${truncate(d.artist_name, 20)}`
          : `${truncate(d.track_name, 25)} - ${truncate(d.artist_name, 20)}`,
  }));
```

<div class="card">
    <div style="display: flex; align-items: center; justify-content: space-between;">
        <h2 style="margin: 0;">${viewType} by count of weeks with at least one play</h2>
        <div style="display: flex; gap: 16px; align-items: center;">
            ${viewType === "Artists" ? includeFeaturesInput : null}
            ${viewTypeInput}
        </div>
    </div>
    ${resize((width) => Plot.plot({
            width,
            marginLeft: viewType === "Artists" ? 120 : 200,
            marginRight: 40,
            marginTop: 0,
            x: { label: "Listening weeks" },
            y: {
                label: null,
                domain: displayNames
            },
            color: {
                legend: true,
                label: "Year",
                type: "ordinal",
                tickFormat: ".0f",
                scheme: "spectral"
            },
            marks: [
                Plot.barX(filteredRaw, {
                    x: viewType === "Artists" && includeFeatures === "Include features" ? "listening_weeks_with_features" : "listening_weeks",
                    y: "display_name",
                    fill: "year",
                    sort: { y: "-x", reduce: "sum" }
                }),
                Plot.text(summaryDataWithYears, {
                    x: (d) => d.total_weeks / 2,
                    y: "display_name",
                    text: (d) => d.label_text,
                    fill: "black",
                    anchor: "middle"
                }),
                Plot.ruleX([0])
            ]
        })
    )}

</div>
