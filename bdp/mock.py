from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from types import ModuleType

METADATA_LINE_RE = re.compile(
    r"mock\.(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)"
)


def discover_mocks(input_root: Path) -> list[Path]:
    """Discover all mock generator files in input directories."""
    mock_paths: list[Path] = []
    if not input_root.exists():
        return mock_paths
    for path in input_root.rglob("*.mock.py"):
        if not path.is_file():
            continue
        if path.name.startswith("_"):
            continue
        if "__pycache__" in path.parts:
            continue
        mock_paths.append(path)
    return sorted(mock_paths)


def parse_mock_metadata(path: Path) -> dict[str, str]:
    """Parse mock metadata from file comments."""
    source = path.read_text(encoding="utf-8")
    lines, _ = extract_metadata_lines(source, "#")
    metadata: dict[str, str] = {}
    for line in lines:
        if not line.startswith("mock."):
            continue
        match = METADATA_LINE_RE.fullmatch(line)
        if match is None:
            raise ValueError(f"Invalid mock metadata line in {path}: {line}")
        key = match.group("key")
        value = match.group("value").strip()
        if key in metadata:
            raise ValueError(f"Duplicate mock.{key} in {path}")
        metadata[key] = value
    return metadata


def extract_metadata_lines(source: str, prefix: str) -> tuple[list[str], list[str]]:
    """Extract metadata comment lines from source file."""
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


def generate_all_mocks(input_root: Path, force: bool = False) -> None:
    """Generate all mock data files."""
    mock_paths = discover_mocks(input_root)
    if not mock_paths:
        print("No mock generators found.")
        return

    print(f"Found {len(mock_paths)} mock generator(s)...")
    for mock_path in mock_paths:
        generate_mock(mock_path, force)


def generate_mock(mock_path: Path, force: bool = False) -> None:
    """Generate mock data for a single mock file."""
    metadata = parse_mock_metadata(mock_path)

    if "output" not in metadata:
        raise ValueError(f"Missing required mock.output in {mock_path}")

    output_filename = metadata["output"]
    output_path = mock_path.parent / output_filename

    # Check if output already exists
    if output_path.exists() and not force:
        response = input(
            f"Output file '{output_path}' already exists. Overwrite? [y/N]: "
        )
        if response.lower() not in ("y", "yes"):
            print(f"Skipping {mock_path.name}")
            return

    # Load and execute the mock generator
    module = load_mock_module(mock_path)
    generate_func = getattr(module, "generate", None)
    if generate_func is None or not callable(generate_func):
        raise ValueError(
            f"Mock file {mock_path} must define a callable 'generate' function"
        )

    data = generate_func()

    # Write output based on file extension
    write_output(data, output_path)
    print(f"Generated: {output_path}")


def write_output(data, output_path: Path) -> None:
    """Write mock data to output file based on extension."""
    suffix = output_path.suffix.lower()

    if suffix == ".json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    elif suffix == ".csv":
        import csv

        if not data:
            output_path.write_text("")
            return
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            fieldnames = list(data[0].keys())
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
        else:
            raise ValueError(f"CSV output requires list of dicts, got {type(data)}")
    elif suffix == ".parquet":
        import polars as pl
        import pyarrow.parquet as pq

        if isinstance(data, pl.DataFrame):
            arrow_table = data.to_arrow()
        elif isinstance(data, list):
            df = pl.DataFrame(data)
            arrow_table = df.to_arrow()
        else:
            raise ValueError(f"Unsupported data type for parquet: {type(data)}")

        if output_path.exists():
            output_path.unlink()
        pq.write_table(arrow_table, output_path)
    else:
        raise ValueError(f"Unsupported output format: {suffix}")


def load_mock_module(module_path: Path) -> ModuleType:
    """Load a mock module from file path."""
    module_name = f"mock_{module_path.stem}"
    module_spec = importlib.util.spec_from_file_location(module_name, module_path)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError(f"Unable to load mock module: {module_path}")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module
