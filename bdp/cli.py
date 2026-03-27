from __future__ import annotations

import argparse
from pathlib import Path

from bdp.api import find_assets_root
from bdp.materialize import (
    check_asset_bodies,
    check_asset_filenames,
    check_dependencies_exist,
    check_dependency_cycles,
    check_duplicate_dependencies,
    discover_assets,
    materialize,
)
from bdp.mock import generate_all_mocks

CHECK_RULES = (
    ("File name matches asset.name", check_asset_filenames),
    ("All dependencies exist", check_dependencies_exist),
    ("No dependency cycles", check_dependency_cycles),
    ("Asset files have content beyond metadata", check_asset_bodies),
    ("No duplicate dependencies", check_duplicate_dependencies),
)


def _materialize(args: argparse.Namespace) -> None:
    materialize(args.assets)


def _check(_: argparse.Namespace) -> None:
    for rule, func in CHECK_RULES:
        try:
            func()
        except Exception:
            print(f"{rule}: FAIL")
            raise
        print(f"{rule}: OK")


def _list_assets(_: argparse.Namespace) -> None:
    assets_root = find_assets_root()
    assets = discover_assets(assets_root)
    if not assets:
        print("No assets found.")
        return
    for key in sorted(assets):
        asset = assets[key]
        rel_path = asset.path.relative_to(assets_root)
        print(f"- {asset.key} [{asset.kind}] ({rel_path})")
        if asset.description:
            print(f"  description: {asset.description}")
        for index, dep in enumerate(asset.depends):
            connector = "└─" if index == len(asset.depends) - 1 else "├─"
            print(f"  {connector} {dep}")


def _mock(args: argparse.Namespace) -> None:
    input_root = Path.cwd() / "input"
    generate_all_mocks(input_root, force=args.force)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="bdp",
        description="Barefoot Data Platform CLI.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    materialize_parser = subparsers.add_parser(
        "materialize",
        help="Materialize assets into parquet files.",
        description="Materialize assets into parquet files. Defaults to all assets.",
    )
    materialize_parser.add_argument(
        "assets",
        nargs="*",
        metavar="ASSET",
        help="Asset keys to materialize. Defaults to all assets.",
    )
    materialize_parser.set_defaults(func=_materialize, parser=materialize_parser)

    check_parser = subparsers.add_parser(
        "check",
        help="Validate assets.",
    )
    check_parser.set_defaults(func=_check)

    list_parser = subparsers.add_parser(
        "list",
        help="List available assets.",
    )
    list_parser.set_defaults(func=_list_assets)

    mock_parser = subparsers.add_parser(
        "mock",
        help="Generate mock input data.",
        description=(
            "Generate mock input data from .mock.py files in input/ directories."
        ),
    )
    mock_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files without prompting.",
    )
    mock_parser.set_defaults(func=_mock)

    args = parser.parse_args()
    args.func(args)
