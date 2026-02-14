"""Tests for the featured_artists utility module."""

import pytest

from .featured_artists import extract_featured_artists


class TestExtractFeaturedArtists:
    """Test cases for extract_featured_artists function."""

    @pytest.mark.parametrize(
        "track_name,expected",
        [
            (None, []),
            ("", []),
            ("Tate & Lyle - VIP", []),
            ("Start Again", []),
            ("Glitter & Gold", []),
            # Edge cases: "with" in song titles should not be treated as features
            ("Walk With Me", []),
            ("Stay With Me", []),
            ("Alone with You", []),
            ("Away With Me", []),
        ],
    )
    def test_basic_inputs_and_edge_cases(self, track_name, expected):
        """Test empty/None inputs and tracks without featured artists."""
        assert extract_featured_artists(track_name) == expected

    @pytest.mark.parametrize(
        "track_name,expected",
        [
            # feat. patterns
            ("Talk Up (feat. JAY-Z)", ["JAY-Z"]),
            ("Weaker (Feat. Dena Amy)", ["Dena Amy"]),
            ("Afterlife (feat. bailey)", ["bailey"]),
            # Bracket patterns
            (
                "Satisfaction (Radio Edit) [feat. Larcy]",
                ["Larcy"],
            ),
            (
                "Spiritual (Mriya) [feat. Brooke Tomlinson]",
                ["Brooke Tomlinson"],
            ),
            # ft. abbreviations
            ("Young Jedi (ft. Dizzy Wright)", ["Dizzy Wright"]),
            (
                "All For You (ft. Kaleena Zanders)",
                ["Kaleena Zanders"],
            ),
            # featuring full word
            (
                "The Answer (featuring Arthur Baker & Victor Simonelli)",
                ["Arthur Baker & Victor Simonelli"],
            ),
            ("Lost (featuring Muri)", ["Muri"]),
            # with pattern
            ("Unlearn (with Gracie Abrams)", ["Gracie Abrams"]),
            (
                "Love/Hate Letter to Alcohol (with Fleet Foxes)",
                ["Fleet Foxes"],
            ),
        ],
    )
    def test_pattern_matching(self, track_name, expected):
        """Test various feature pattern matching."""
        assert extract_featured_artists(track_name) == expected

    @pytest.mark.parametrize(
        "track_name,expected",
        [
            ("Song (feat. Artist)", ["Artist"]),
            ("Song (Feat. Artist)", ["Artist"]),
            ("Song (FEAT. Artist)", ["Artist"]),
            ("Song (ft. Artist)", ["Artist"]),
            ("Song (Ft. Artist)", ["Artist"]),
            ("Song (with Artist)", ["Artist"]),
            ("Song (With Artist)", ["Artist"]),
            ("Song (WITH Artist)", ["Artist"]),
        ],
    )
    def test_case_insensitivity(self, track_name, expected):
        """Test that patterns are matched case-insensitively."""
        assert extract_featured_artists(track_name) == expected

    @pytest.mark.parametrize(
        "track_name,expected",
        [
            # Multiple comma-separated artists
            (
                "Problemz (feat. Erick The Architect, CJ Fly, "
                "The Underachievers, Zombie Juice & Nyck Caution)",
                [
                    "Erick The Architect",
                    "CJ Fly",
                    "The Underachievers",
                    "Zombie Juice & Nyck Caution",
                ],
            ),
            (
                "Taki Taki (with Selena Gomez, Ozuna & Cardi B)",
                ["Selena Gomez", "Ozuna & Cardi B"],
            ),
            # Nested feat patterns
            (
                "Lifestyle (with Bas feat. A$AP Ferg)",
                ["Bas", "A$AP Ferg"],
            ),
            (
                "Passcode (with Ari Lennox feat. Buddy, Smino, Mez & Guapdad 4000)",
                ["Ari Lennox", "Buddy", "Smino", "Mez & Guapdad 4000"],
            ),
            (
                "11 Minutes (with Halsey feat. Travis Barker)",
                ["Halsey", "Travis Barker"],
            ),
            # Feat outside parens + remixer
            (
                "Stay feat. Alessia Cara (Krio Remix)",
                ["Alessia Cara", "Krio"],
            ),
            (
                "End Of The Night feat Dorrough Music (Prod by Tha Bizness)",
                ["Dorrough Music"],
            ),
            # Edge case: artist name with comma should not be split
            (
                "deathwish (feat. nothing,nowhere.)",
                ["nothing,nowhere."],
            ),
        ],
    )
    def test_complex_parsing(self, track_name, expected):
        """Test complex parsing scenarios."""
        assert extract_featured_artists(track_name) == expected

    def test_trailing_dash_cleanup(self):
        """Test that trailing dashes are cleaned up."""
        result = extract_featured_artists(
            "Made In France (with Tchami & Malaa, feat. Mercer)"
        )
        assert "Tchami & Malaa" in result
        assert "Mercer" in result
        assert "Tchami & Malaa," not in result  # Should not have trailing comma

    @pytest.mark.parametrize(
        "track_name,expected",
        [
            (
                "Young Jedi (ft. Dizzy Wright) (Prod by 6ix) (DatPiff Exclusive)",
                ["Dizzy Wright"],
            ),
            (
                "Welcome To Forever (ft. Jon Bellion) (Prod by 6ix)",
                ["Jon Bellion"],
            ),
        ],
    )
    def test_excludes_producer_credits(self, track_name, expected):
        """Test that producer credits are excluded."""
        assert extract_featured_artists(track_name) == expected

    @pytest.mark.parametrize(
        "track_name,expected",
        [
            # Generic remix/version exclusions (no artist names)
            ("Outlaw (Original Mix)", []),
            ("Insomnia (Extended Version)", []),
            ("Song (Radio Edit)", []),
            ("Track (VIP)", []),
            ("Music (Club Mix)", []),
            # Remixers extracted as featured artists
            ("Rain (Mitis Remix)", ["Mitis"]),
            (
                "Looking For Diversion (Lenzman & Duskee Remix)",
                ["Lenzman", "Duskee"],
            ),
            (
                "Made In France (with Tchami & Malaa, feat. Mercer) - Wax Motif Remix",
                ["Tchami & Malaa", "Mercer", "Wax Motif"],
            ),
            # Exclusive label exclusions
            (
                "Young Jedi (ft. Dizzy Wright) (DatPiff Exclusive)",
                ["Dizzy Wright"],
            ),
            # Complex real-world examples with exclusions
            (
                "Joy In Eyes (feat. Bonnie) - Original Mix",
                ["Bonnie"],
            ),
            (
                "Energy (with A$AP Rocky & Sabrina Claudio) "
                "(feat. Sabrina Claudio) - BURNS' Extra Energy Edit",
                [
                    "A$AP Rocky & Sabrina Claudio",
                    "Sabrina Claudio",
                    "BURNS' Extra Energy",
                ],
            ),
            # Edge cases: dash remix should not match song title words
            (
                "Away With Me - Calibre Remix",
                ["Calibre"],
            ),
            # Edge cases: genre descriptors should not be treated as artists
            (
                "Run It Back (feat. Caroline Byrne) - Drum & Bass Edit",
                ["Caroline Byrne"],
            ),
            # Edge cases: descriptor words at end of artist names
            (
                "Burns - Lane 8 Club Mix",
                ["Lane 8"],
            ),
            (
                "You Are In My System - Faster Horses Sport Mix",
                ["Faster Horses"],
            ),
            # But "Club Angel" is an artist name, not a descriptor
            (
                "Feel The Friction (Club Angel Remix)",
                ["Club Angel"],
            ),
        ],
    )
    def test_remix_and_version_handling(self, track_name, expected):
        """Test that remixers are extracted but generic descriptors are excluded."""
        assert extract_featured_artists(track_name) == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
