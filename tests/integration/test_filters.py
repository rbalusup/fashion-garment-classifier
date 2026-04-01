"""Integration tests for filter_garments() — 16 location + time filter cases.

All tests use the shared seeded session (12 garments). No API calls.
"""

import pytest
from sqlalchemy.orm import Session

from fashion_api.garment.filters import filter_garments


def ids(result) -> set[str]:  # type: ignore[no-untyped-def]
    """Extract original_filenames from PaginatedGarments for easy assertion."""
    return {item.image_path.split("/")[-1].replace(".jpg", "") for item in result.items}


# ---------------------------------------------------------------------------
# Location filters
# ---------------------------------------------------------------------------

class TestLocationFilters:

    def test_filter_by_continent_europe(self, db_session: Session) -> None:
        result = filter_garments(db_session, continent="europe", limit=100)
        assert ids(result) == {"g001", "g002", "g003", "g010"}

    def test_filter_by_continent_asia(self, db_session: Session) -> None:
        result = filter_garments(db_session, continent="asia", limit=100)
        assert ids(result) == {"g004", "g005"}

    def test_filter_by_continent_americas(self, db_session: Session) -> None:
        result = filter_garments(db_session, continent="americas", limit=100)
        assert ids(result) == {"g006", "g007", "g008", "g009"}

    def test_filter_by_country_usa(self, db_session: Session) -> None:
        result = filter_garments(db_session, country="usa", limit=100)
        assert ids(result) == {"g006", "g007", "g009"}

    def test_filter_by_country_japan(self, db_session: Session) -> None:
        result = filter_garments(db_session, country="japan", limit=100)
        assert ids(result) == {"g004", "g005"}

    def test_filter_by_city_paris(self, db_session: Session) -> None:
        result = filter_garments(db_session, city="paris", limit=100)
        assert len(result.items) == 1
        assert ids(result) == {"g001"}

    def test_filter_by_city_tokyo(self, db_session: Session) -> None:
        result = filter_garments(db_session, city="tokyo", limit=100)
        assert ids(result) == {"g004", "g005"}

    def test_filter_continent_and_country_combined(self, db_session: Session) -> None:
        """Both continent and country must match."""
        result = filter_garments(db_session, continent="americas", country="usa", limit=100)
        assert ids(result) == {"g006", "g007", "g009"}

    def test_filter_all_three_location_levels(self, db_session: Session) -> None:
        result = filter_garments(
            db_session, continent="asia", country="japan", city="tokyo", limit=100
        )
        assert ids(result) == {"g004", "g005"}

    def test_unknown_continent_returns_empty(self, db_session: Session) -> None:
        result = filter_garments(db_session, continent="antarctica", limit=100)
        assert result.total == 0
        assert result.items == []

    def test_mismatched_continent_country_returns_empty(self, db_session: Session) -> None:
        """France is in Europe, not Asia — should return empty."""
        result = filter_garments(db_session, continent="asia", country="france", limit=100)
        assert result.total == 0


# ---------------------------------------------------------------------------
# Time filters
# ---------------------------------------------------------------------------

class TestTimeFilters:

    def test_filter_by_year_2024(self, db_session: Session) -> None:
        result = filter_garments(db_session, year=2024, limit=100)
        result_ids = ids(result)
        # 2024 garments: g001, g002, g004, g006 (wait - g006 is 2023), g007, g008, g011
        assert "g001" in result_ids  # 2024-03-15
        assert "g002" in result_ids  # 2024-07-22
        assert "g003" not in result_ids  # 2025-01-10
        assert "g006" not in result_ids  # 2023-08-19

    def test_filter_by_year_2025(self, db_session: Session) -> None:
        result = filter_garments(db_session, year=2025, limit=100)
        result_ids = ids(result)
        assert "g003" in result_ids  # 2025-01-10
        assert "g005" in result_ids  # 2025-02-28
        assert "g009" in result_ids  # 2025-03-03
        assert "g012" in result_ids  # 2025-01-25
        assert "g001" not in result_ids  # 2024

    def test_filter_by_month_january_across_all_years(self, db_session: Session) -> None:
        result = filter_garments(db_session, month=1, limit=100)
        result_ids = ids(result)
        assert "g003" in result_ids  # 2025-01-10
        assert "g012" in result_ids  # 2025-01-25

    def test_filter_by_year_and_month(self, db_session: Session) -> None:
        result = filter_garments(db_session, year=2025, month=1, limit=100)
        result_ids = ids(result)
        assert "g003" in result_ids  # 2025-01-10
        assert "g012" in result_ids  # 2025-01-25
        assert "g005" not in result_ids  # 2025-02-28 (wrong month)

    def test_location_and_time_combined_europe_2024(self, db_session: Session) -> None:
        result = filter_garments(db_session, continent="europe", year=2024, limit=100)
        result_ids = ids(result)
        assert "g001" in result_ids  # europe, 2024-03-15
        assert "g002" in result_ids  # europe, 2024-07-22
        assert "g003" not in result_ids  # europe but 2025

    def test_no_filters_returns_all_12(self, db_session: Session) -> None:
        result = filter_garments(db_session, limit=100)
        assert result.total == 12
