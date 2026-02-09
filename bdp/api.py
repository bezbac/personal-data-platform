from __future__ import annotations

from pathlib import Path

import chdb
import pyarrow as pa


def sql(statement: str, params: dict[str, object] | None = None) -> pa.Table:
    """Execute SQL using chDB and return results as a PyArrow Table."""
    if params:
        for key, value in params.items():
            statement = statement.replace(f"{{{key}}}", str(value))
    result = chdb.query(statement, "Arrow")
    return result


def table(path: Path) -> pa.Table:
    """Read a parquet file using chDB's file() function."""
    escaped_path = str(path).replace("'", "''")
    result = chdb.query(f"SELECT * FROM file('{escaped_path}')", "Arrow")
    return result


def find_assets_root() -> Path:
    for parent in [Path.cwd(), *Path.cwd().parents]:
        candidate = parent / "assets"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("assets directory not found")
