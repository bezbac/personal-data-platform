"""Utilities for extracting featured artists from track names."""

import re


def extract_featured_artists(track_name: str | None) -> list[str]:
    """Extract featured artists from track name.

    Patterns matched:
    - (feat. Artist), [feat. Artist]
    - (ft. Artist), (Ft. Artist)
    - (with Artist) - only inside parentheses, not standalone
    - (featuring Artist), (Featuring Artist)
    - Also matches feat. outside parentheses

    Edge cases excluded (not features):
    - Producer credits: (Prod by ...), (produced by ...)
    - Exclusives: (DatPiff Exclusive)
    - Generic descriptors: (Edit), (VIP), (Radio Edit) without artist names
    - Genre descriptors: Drum & Bass, etc.

    Multiple artists are split on commas only (preserving & as part of names).
    Nested feat patterns are extracted recursively (e.g., "with Bas feat. X").

    Examples:
        >>> extract_featured_artists(None)
        []
        >>> extract_featured_artists("")
        []
        >>> extract_featured_artists("Start Again")
        []
        >>> extract_featured_artists("Talk Up (feat. JAY-Z)")
        ['JAY-Z']
        >>> extract_featured_artists("[feat. Larcy]")
        ['Larcy']
        >>> extract_featured_artists("Problemz (feat. Alice, Bob & Carol)")
        ['Alice', 'Bob & Carol']
        >>> extract_featured_artists("Lifestyle (with Bas feat. A$AP Ferg)")
        ['Bas', 'A$AP Ferg']
        >>> extract_featured_artists("Song (ft. Artist)")
        ['Artist']
        >>> extract_featured_artists("Song (Featuring Artist)")
        ['Artist']
        >>> extract_featured_artists("Stay feat. Alessia Cara (Krio Remix)")
        ['Alessia Cara', 'Krio']
        >>> extract_featured_artists("Rain (Mitis Remix)")
        ['Mitis']
        >>> extract_featured_artists("Looking For Diversion (Lenzman & Duskee Remix)")
        ['Lenzman', 'Duskee']
        >>> extract_featured_artists("Song (Radio Edit)")
        []
        >>> extract_featured_artists("Walk With Me")  # "With" in title, not feature
        []
        >>> extract_featured_artists("deathwish (feat. nothing,nowhere.)")
        ['nothing,nowhere.']
    """
    if not track_name:
        return []

    featured: list[str] = []
    processed_spans: set[tuple[int, int]] = set()

    # Regex pattern to match feature indicators
    # Matches: feat., ft., Ft., featuring, Featuring, with
    # Inside parentheses/brackets or standalone before parentheses
    # NOTE: "with" must be inside parentheses/brackets to avoid matching
    # song titles like "Walk With Me"
    pattern = (
        r"(?:\(|\[)(?:feat\.?|ft\.?|Ft\.?|featuring|Featuring|with)\s+"
        r"([^\)\]]+?)(?:\)|\]|$|(?=\())"
    )

    # Also match feat./ft. outside parentheses (standalone)
    standalone_pattern = (
        r"\s(?:feat\.?|ft\.?|Ft\.?|featuring|Featuring)\s+"
        r"([^\(\[]+?)(?=\s*(?:\(|\[|$))"
    )

    # Find all matches, avoiding duplicates
    for pattern_to_use in [pattern, standalone_pattern]:
        for match in re.finditer(pattern_to_use, track_name, re.IGNORECASE):
            span = match.span()
            # Skip if this span overlaps with already processed content
            if any(span[0] < end and span[1] > start for start, end in processed_spans):
                continue
            processed_spans.add(span)

            content = match.group(1).strip()

            # Skip producer credits
            if re.search(r"^(Prod\.?\s+by|produced\s+by)", content, re.IGNORECASE):
                continue

            # Skip exclusives
            if re.search(r"DatPiff\s+Exclusive", content, re.IGNORECASE):
                continue

            # Extract artists from remix/version patterns
            # (e.g., "Artist Remix", "Artist1 & Artist2 Remix")
            # Only extract if there's actual artist content before the
            # remix/mix/version/edit keyword
            remix_match = re.search(
                r"^(.+?)\s+(Remix|Mix|Version|Edit)$", content, re.IGNORECASE
            )
            if remix_match:
                artists_part = remix_match.group(1).strip()
                # Only extract if it looks like artist names
                # (not generic descriptors)
                # Skip if it's just a descriptor word like
                # "Radio", "Original", "Extended", "VIP"
                if not re.search(
                    r"^(Radio|Original|Extended|VIP|Club|Main)\s*",
                    artists_part,
                    re.IGNORECASE,
                ):
                    content = artists_part
                else:
                    continue

            # Check for nested feat patterns (e.g., "with Bas feat. A$AP Ferg")
            # Split the content at any nested feat/ft/featuring pattern
            parts = re.split(
                r"\s+(?:feat\.?|ft\.?|Ft\.?|featuring|Featuring)\s+",
                content,
                flags=re.IGNORECASE,
            )

            # Process each part for comma-separated artists
            for part in parts:
                part = part.strip()
                if not part or len(part) <= 1:
                    continue

                # Split on commas followed by space to get individual artists
                # This preserves artist names with commas like "nothing,nowhere."
                # But we also need to handle trailing commas
                artists = [a.strip().rstrip(",") for a in part.split(", ")]

                # Clean up each artist name
                for artist in artists:
                    # Remove trailing punctuation but keep internal punctuation
                    artist = artist.strip(" -")
                    if artist and len(artist) > 1:
                        featured.append(artist)

    def _process_remixer_content(content: str) -> None:
        """Process remixer content and add artists to featured list."""
        # Skip generic descriptors without artist names
        if re.search(
            r"^(Radio|Original|Extended|VIP|Club|Main)\s*$", content, re.IGNORECASE
        ):
            return

        # Skip genre descriptors
        if re.search(
            r"^(Drum\s*&\s*Bass|House|Techno|Trance|Dubstep|Trap|Hip\s*Hop|"
            r"R\s*&\s*B|Electronic|Dance|Pop|Rock|Metal|Jazz|Classical)\s*$",
            content,
            re.IGNORECASE,
        ):
            return

        # Strip trailing descriptor words from artist names
        # e.g., "Lane 8 Club" -> "Lane 8", "Faster Horses Sport" -> "Faster Horses"
        content = re.sub(
            r"\s+(Club|Sport|Radio|Edit|VIP|Main|Original|Extended)\s*$",
            "",
            content,
            flags=re.IGNORECASE,
        )

        # Split on commas and & to get individual artists
        # First split by comma, then split each part by &
        for comma_part in content.split(","):
            comma_part = comma_part.strip()
            for artist in comma_part.split("&"):
                artist = artist.strip().strip(" -")
                if artist and len(artist) > 1:
                    featured.append(artist)

    # Also match remixer patterns like "(Artist Remix)" without feat indicator
    remix_pattern = r"\(([^)]+?)\s+(Remix|Mix)\)"
    remix_matches = re.finditer(remix_pattern, track_name, re.IGNORECASE)

    # Match remixers after dash (e.g., "- Wax Motif Remix", "- Artist Edit")
    # But be careful not to match song title words before the dash
    # The pattern requires capital letters at the start to avoid matching
    # words like "Me" from "Away With Me"
    dash_remix_pattern = (
        r"-\s*([A-Z][^-(]*?(?:\s+&\s+[A-Z][^-(]*?)?)\s+"
        r"(Remix|Mix|Edit)\s*$"
    )
    dash_matches = re.finditer(dash_remix_pattern, track_name, re.IGNORECASE)

    # Process remixer matches in parentheses
    for match in remix_matches:
        _process_remixer_content(match.group(1).strip())

    # Process remixer matches after dash
    for match in dash_matches:
        _process_remixer_content(match.group(1).strip())

    return featured
