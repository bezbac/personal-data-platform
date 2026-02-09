from __future__ import annotations

import importlib.util
import re
from collections.abc import Iterable
from dataclasses import dataclass
from graphlib import CycleError, TopologicalSorter
from pathlib import Path
from types import ModuleType
from typing import Literal

import chdb
import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq

from bdp.api import find_assets_root

AssetKind = Literal["python", "sql"]
ASSET_SUFFIXES: dict[str, AssetKind] = {
    ".py": "python",
    ".sql": "sql",
}
COMMENT_PREFIXES: dict[AssetKind, str] = {"python": "#", "sql": "--"}
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
METADATA_LINE_RE = re.compile(
    r"asset\.(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)"
)

# Pattern to match table references in SQL
TABLE_REF_RE = re.compile(
    r"\{\{\s*ref\(\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?\s*\)\s*\}\}"
)


@dataclass(frozen=True)
class Asset:
    name: str
    key: str
    path: Path
    kind: AssetKind
    depends: tuple[str, ...]
    description: str | None


def asset_parquet_path(asset: Asset) -> Path:
    """Generate the parquet file path for an asset."""
    return asset.path.parent / f"{asset.name}.parquet"


def materialize(
    names: Iterable[str] | None = None,
) -> None:
    assets_root = find_assets_root()
    assets = discover_assets(assets_root)
    deps_map = asset_dependencies(assets)
    selected = resolve_selection(names, assets, deps_map)
    graph = {key: deps_map[key] for key in selected}
    try:
        order = list(TopologicalSorter(graph).static_order())
    except CycleError as exc:
        raise ValueError(f"Dependency cycle detected: {exc}") from exc

    print(f"Materializing {len(order)} asset(s)...")
    for key in order:
        asset = assets[key]
        print(f"  -> {asset.key}")
        if asset.kind == "sql":
            materialize_sql(asset, assets)
            continue
        if asset.kind == "python":
            materialize_python(asset)
            continue
        print(f"Skipping unsupported asset type '{asset.kind}' for {asset.path}")
    print("Done.")


def check_assets() -> None:
    check_asset_filenames()
    check_dependencies_exist()
    check_dependency_cycles()
    check_asset_bodies()
    check_duplicate_dependencies()


def check_asset_filenames() -> None:
    assets_root = find_assets_root()
    for path in asset_files(assets_root):
        kind = ASSET_SUFFIXES[path.suffix]
        source = path.read_text(encoding="utf-8")
        metadata, _ = metadata_from_source(path, kind, source)
        name = single_metadata_value(metadata, "name", path)
        validate_identifier(name, "table", path)
        validate_asset_filename(path, name)


def check_dependencies_exist() -> None:
    deps_map = build_dependency_map(find_assets_root(), check_dep_duplicates=False)
    validate_dependency_map(deps_map)


def check_dependency_cycles() -> None:
    deps_map = build_dependency_map(find_assets_root(), check_dep_duplicates=False)
    graph = validate_dependency_map(deps_map)
    try:
        list(TopologicalSorter(graph).static_order())
    except CycleError as exc:
        raise ValueError(f"Dependency cycle detected: {exc}") from exc


def check_asset_bodies() -> None:
    assets_root = find_assets_root()
    for path in asset_files(assets_root):
        kind = ASSET_SUFFIXES[path.suffix]
        source = path.read_text(encoding="utf-8")
        _, body_lines = metadata_from_source(path, kind, source)
        ensure_asset_body(body_lines, path)


def check_duplicate_dependencies() -> None:
    assets_root = find_assets_root()
    for path in asset_files(assets_root):
        kind = ASSET_SUFFIXES[path.suffix]
        source = path.read_text(encoding="utf-8")
        metadata, _ = metadata_from_source(path, kind, source)
        parse_dependencies(metadata.get("depends", []), path, check_duplicates=True)


def build_dependency_map(
    assets_root: Path,
    *,
    check_dep_duplicates: bool,
) -> dict[str, tuple[Path, tuple[str, ...]]]:
    deps_map: dict[str, tuple[Path, tuple[str, ...]]] = {}
    for path in asset_files(assets_root):
        kind = ASSET_SUFFIXES[path.suffix]
        source = path.read_text(encoding="utf-8")
        name, _, depends = parse_asset_metadata(
            path,
            kind,
            source,
            require_body=False,
            check_dep_duplicates=check_dep_duplicates,
        )
        key = f"{name}"
        if key in deps_map:
            raise ValueError(f"Duplicate asset key: {key}")
        deps_map[key] = (path, depends)
    return deps_map


def validate_dependency_map(
    deps_map: dict[str, tuple[Path, tuple[str, ...]]],
) -> dict[str, list[str]]:
    graph: dict[str, list[str]] = {}
    for key, (path, depends) in deps_map.items():
        deps: list[str] = []
        for dep_name in depends:
            if dep_name == key:
                raise ValueError(f"Asset {key} depends on itself")
            if dep_name not in deps_map:
                raise ValueError(
                    f"Unknown dependency '{dep_name}' referenced in {path}"
                )
            deps.append(dep_name)
        graph[key] = sorted(set(deps))
    return graph


def discover_assets(assets_root: Path) -> dict[str, Asset]:
    assets: dict[str, Asset] = {}
    for path in asset_files(assets_root):
        asset = asset_from_path(path)
        if asset.key in assets:
            raise ValueError(f"Duplicate asset key: {asset.key}")
        assets[asset.key] = asset
    return assets


def asset_dependencies(assets: dict[str, Asset]) -> dict[str, list[str]]:
    deps_map: dict[str, list[str]] = {}
    for key, asset in assets.items():
        deps: list[str] = []
        for dep_name in asset.depends:
            if dep_name == key:
                raise ValueError(f"Asset {key} depends on itself")
            if dep_name not in assets:
                raise ValueError(
                    f"Unknown dependency '{dep_name}' referenced in {asset.path}"
                )
            deps.append(dep_name)
        deps_map[key] = sorted(deps)
    return deps_map


def resolve_selection(
    names: Iterable[str] | None,
    assets: dict[str, Asset],
    deps_map: dict[str, list[str]],
) -> set[str]:
    if not names:
        selected = set(assets)
    else:
        requested = list(names)
        unknown = sorted(set(requested) - set(assets))
        if unknown:
            raise ValueError(f"Unknown assets: {', '.join(unknown)}")
        selected = set(requested)
    stack = list(selected)
    while stack:
        key = stack.pop()
        for dep in deps_map[key]:
            if dep not in selected:
                selected.add(dep)
                stack.append(dep)
    return selected


def asset_files(assets_root: Path) -> list[Path]:
    asset_paths: list[Path] = []
    for path in assets_root.rglob("*"):
        if not path.is_file():
            continue
        if path.name.startswith("_"):
            continue
        if "__pycache__" in path.parts:
            continue
        if path.suffix not in ASSET_SUFFIXES:
            continue
        asset_paths.append(path)
    return sorted(asset_paths)


def asset_from_path(path: Path) -> Asset:
    kind = ASSET_SUFFIXES[path.suffix]
    source = path.read_text(encoding="utf-8")
    name, description, depends = parse_asset_metadata(path, kind, source)
    validate_asset_filename(path, name)
    key = f"{name}"
    return Asset(
        name=name,
        key=key,
        path=path,
        kind=kind,
        depends=depends,
        description=description,
    )


def parse_asset_metadata(
    path: Path,
    kind: AssetKind,
    source: str,
    *,
    require_body: bool = True,
    check_dep_duplicates: bool = True,
) -> tuple[str, str | None, tuple[str, ...]]:
    metadata, body_lines = metadata_from_source(path, kind, source)
    name = single_metadata_value(metadata, "name", path)
    validate_identifier(name, "table", path)
    description = optional_metadata_value(metadata, "description", path)
    depends = parse_dependencies(
        metadata.get("depends", []),
        path,
        check_duplicates=check_dep_duplicates,
    )
    if require_body:
        ensure_asset_body(body_lines, path)
    return name, description, tuple(depends)


def extract_metadata_lines(source: str, prefix: str) -> tuple[list[str], list[str]]:
    lines: list[str] = []
    source_lines = source.splitlines()
    body_start = len(source_lines)
    for index, line in enumerate(source_lines):
        stripped = line.lstrip()
        if not stripped:
            if not lines:
                continue
            continue
        if stripped.startswith("#!") and not lines:
            continue
        if stripped.startswith(prefix):
            content = stripped[len(prefix) :].lstrip()
            if content:
                lines.append(content)
            continue
        body_start = index
        break
    if body_start >= len(source_lines):
        return lines, []
    return lines, source_lines[body_start:]


def metadata_from_source(
    path: Path,
    kind: AssetKind,
    source: str,
) -> tuple[dict[str, list[str]], list[str]]:
    prefix = COMMENT_PREFIXES[kind]
    lines, body_lines = extract_metadata_lines(source, prefix)
    if not lines:
        raise ValueError(f"Missing asset metadata in {path}")
    metadata = parse_metadata_lines(lines, path)
    return metadata, body_lines


def parse_metadata_lines(lines: list[str], path: Path) -> dict[str, list[str]]:
    metadata: dict[str, list[str]] = {}
    for line in lines:
        if not line.startswith("asset."):
            continue
        match = METADATA_LINE_RE.fullmatch(line)
        if match is None:
            raise ValueError(f"Invalid asset metadata line in {path}: {line}")
        key = match.group("key")
        value = match.group("value").strip()
        metadata.setdefault(key, []).append(value)
    return metadata


def single_metadata_value(metadata: dict[str, list[str]], key: str, path: Path) -> str:
    if key not in metadata or not metadata[key]:
        raise ValueError(f"Missing asset.{key} in {path}")
    if len(metadata[key]) != 1:
        raise ValueError(f"asset.{key} must appear once in {path}")
    value = metadata[key][0]
    if not value:
        raise ValueError(f"asset.{key} must have a value in {path}")
    return value


def optional_metadata_value(
    metadata: dict[str, list[str]],
    key: str,
    path: Path,
) -> str | None:
    if key not in metadata or not metadata[key]:
        return None
    if len(metadata[key]) != 1:
        raise ValueError(f"asset.{key} must appear once in {path}")
    value = metadata[key][0]
    if not value:
        raise ValueError(f"asset.{key} must have a value in {path}")
    return value


def parse_dependencies(
    values: list[str],
    path: Path,
    *,
    check_duplicates: bool = True,
) -> list[str]:
    deps: list[str] = []
    seen: set[str] = set()
    for raw in values:
        if not raw:
            continue
        parts = [part.strip() for part in raw.split(",")]
        for part in parts:
            if not part:
                continue
            if check_duplicates and part in seen:
                raise ValueError(f"Duplicate dependency '{part}' in {path}")
            validate_asset_reference(part, path)
            seen.add(part)
            deps.append(part)
    return deps


def ensure_asset_body(body_lines: list[str], path: Path) -> None:
    for line in body_lines:
        if line.strip():
            return
    raise ValueError(f"Asset file has no content beyond metadata: {path}")


def validate_asset_filename(path: Path, name: str) -> None:
    if path.stem != name:
        raise ValueError(
            f"Asset file name must match asset.name in {path}. Expected {name}"
        )


def validate_asset_reference(value: str, path: Path) -> None:
    validate_identifier(value, "table", path)


def validate_identifier(value: str, label: str, path: Path) -> None:
    if IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"Invalid {label} name '{value}' from {path}")


def substitute_dependencies(
    sql: str,
    asset: Asset,
    assets: dict[str, Asset],
) -> str:
    """Replace table references with chDB file() function calls."""

    def replace_ref(match: re.Match[str]) -> str:
        table = match.group(1)
        key = f"{table}"

        if key not in assets:
            # This shouldn't happen if validation passed, but just in case
            raise ValueError(
                f"Unknown table reference '{key}' in SQL asset {asset.path}"
            )

        dep_asset = assets[key]
        parquet_path = asset_parquet_path(dep_asset)

        # Check if the dependency file exists
        if not parquet_path.exists():
            raise FileNotFoundError(
                f"Dependency parquet file not found: {parquet_path}. "
                f"Make sure to materialize {key} first."
            )

        # Escape single quotes in path
        escaped_path = str(parquet_path).replace("'", "''")
        return f"file('{escaped_path}')"

    return TABLE_REF_RE.sub(replace_ref, sql)


def materialize_sql(asset: Asset, assets: dict[str, Asset]) -> None:
    source = asset.path.read_text(encoding="utf-8")

    # Extract only the SQL body (without metadata comments)
    _, body_lines = extract_metadata_lines(source, COMMENT_PREFIXES["sql"])
    sql = "\n".join(body_lines).strip()

    if not sql:
        raise ValueError(f"SQL asset is empty: {asset.path}")

    # Substitute table references with file() calls
    sql = substitute_dependencies(sql, asset, assets)

    # Execute SQL via chDB
    result = chdb.query(sql, "ArrowTable")

    # Delete existing parquet file if it exists
    output_path = asset_parquet_path(asset)
    if output_path.exists():
        output_path.unlink()

    # Write result to parquet file
    pq.write_table(result, output_path)


def materialize_python(asset: Asset) -> None:
    module = load_module(asset.path)
    func = getattr(module, asset.name, None)
    if func is None or not callable(func):
        raise ValueError(f"Python asset {asset.path} must define callable {asset.name}")
    result = func()

    # Convert Polars DataFrame to PyArrow Table if needed
    if isinstance(result, pl.DataFrame):
        arrow_table = result.to_arrow()
    elif isinstance(result, pa.Table):
        arrow_table = result
    else:
        raise TypeError("Python assets must return polars.DataFrame or pyarrow.Table")

    # Delete existing parquet file if it exists
    output_path = asset_parquet_path(asset)
    if output_path.exists():
        output_path.unlink()

    # Write result to parquet file
    pq.write_table(arrow_table, output_path)


def load_module(module_path: Path) -> ModuleType:
    module_name = module_name_from_path(module_path)
    module_spec = importlib.util.spec_from_file_location(module_name, module_path)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError(f"Unable to load asset module: {module_path}")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def module_name_from_path(module_path: Path) -> str:
    sanitized = module_path.as_posix().replace("/", "_").replace(".", "_")
    return f"bdp_asset_{sanitized}"
