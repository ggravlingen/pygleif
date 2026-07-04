"""Command-line interface for pygleif.

Usage:
    python -m pygleif <command> [options]

This CLI intentionally uses only the v2 API (``pygleif.v2``). The v1
namespace is retained for backwards compatibility but is planned for
deprecation, so no CLI surface is built on top of it.

Examples:
    python -m pygleif get 5493001KJTIIGC8Y1R12
    python -m pygleif search "bank" --field fulltext --page-size 5
    python -m pygleif search DE000ST8MPP0 --field isin
    python -m pygleif owners 315700WQBDF1ZVVE0T64
    python -m pygleif children 529900IYQRX2JSSIZA36
    python -m pygleif isins 5493001KJTIIGC8Y1R12
    python -m pygleif fuzzy factbook --field entity.legalName
    python -m pygleif fields
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import TYPE_CHECKING

from pygleif.v2 import GleifClient
from pygleif.v2.error import PyGLEIFError

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from pydantic import BaseModel

SEARCH_FIELDS = ("fulltext", "bic", "isin", "lei")


def _dump(model: BaseModel) -> str:
    """Serialize a pydantic model to indented JSON using field aliases."""
    return json.dumps(model.model_dump(by_alias=True, mode="json"), indent=2)


def _record_summary(client: GleifClient, lei: str) -> str:
    """Return a compact one-line summary for a single LEI."""
    record = client.get_lei(lei)
    return json.dumps(
        {
            "lei": record.lei,
            "legal_name": record.legal_name,
            "country": record.country,
        },
        indent=2,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser and its subcommands."""
    parser = argparse.ArgumentParser(
        prog="pygleif",
        description="Query the GLEIF API (v2 client).",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a compact normalized summary instead of the full record.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    get_cmd = sub.add_parser("get", help="Fetch a single LEI record.")
    get_cmd.add_argument("lei", help="The 20-character LEI code.")

    search_cmd = sub.add_parser("search", help="Search LEI records.")
    search_cmd.add_argument("query", help="Search term or code.")
    search_cmd.add_argument(
        "--field",
        choices=SEARCH_FIELDS,
        default="fulltext",
        help="Field to search (default: fulltext).",
    )
    search_cmd.add_argument(
        "--sort",
        default=None,
        help="Sort field, e.g. entity.legalName.",
    )
    search_cmd.add_argument(
        "--page-number",
        type=int,
        default=1,
        help="Page number.",
    )
    search_cmd.add_argument(
        "--page-size",
        type=int,
        default=15,
        help="Results per page.",
    )

    for name, helptext in (
        ("owners", "List parent entities that own the given LEI."),
        ("children", "List child entities owned by the given LEI."),
        ("isins", "List ISINs mapped to the given LEI."),
    ):
        rel_cmd = sub.add_parser(name, help=helptext)
        rel_cmd.add_argument("lei", help="The 20-character LEI code.")
        rel_cmd.add_argument(
            "--page-number",
            type=int,
            default=1,
            help="Page number.",
        )
        rel_cmd.add_argument(
            "--page-size",
            type=int,
            default=15,
            help="Results per page.",
        )

    fuzzy_cmd = sub.add_parser("fuzzy", help="Fuzzy-match legal entity names.")
    fuzzy_cmd.add_argument("query", help="Fuzzy search term.")
    fuzzy_cmd.add_argument(
        "--field",
        default="fulltext",
        help="Field to fuzzy-match (default: fulltext).",
    )

    sub.add_parser("fields", help="List technical metadata for API data fields.")

    return parser


def _cmd_get(client: GleifClient, args: argparse.Namespace) -> str:
    """Handle the ``get`` command."""
    if args.summary:
        return _record_summary(client, args.lei)
    return _dump(client.get_lei_record(args.lei))


def _cmd_search(client: GleifClient, args: argparse.Namespace) -> str:
    """Handle the ``search`` command."""
    return _dump(
        client.search(
            filters={args.field: args.query},
            sort=args.sort,
            page_number=args.page_number,
            page_size=args.page_size,
        ),
    )


def _cmd_owners(client: GleifClient, args: argparse.Namespace) -> str:
    """Handle the ``owners`` command via the documented ``owns`` filter."""
    return _dump(
        client.search(
            filters={"owns": args.lei},
            page_number=args.page_number,
            page_size=args.page_size,
        ),
    )


def _cmd_children(client: GleifClient, args: argparse.Namespace) -> str:
    """Handle the ``children`` command via the ``ownedBy`` filter."""
    return _dump(
        client.search(
            filters={"ownedBy": args.lei},
            page_number=args.page_number,
            page_size=args.page_size,
        ),
    )


def _cmd_isins(client: GleifClient, args: argparse.Namespace) -> str:
    """Handle the ``isins`` command."""
    return _dump(
        client.isins(
            args.lei,
            page_number=args.page_number,
            page_size=args.page_size,
        ),
    )


def _cmd_fuzzy(client: GleifClient, args: argparse.Namespace) -> str:
    """Handle the ``fuzzy`` command."""
    return _dump(client.fuzzy_completions(args.query, field=args.field))


def _cmd_fields(client: GleifClient, args: argparse.Namespace) -> str:  # noqa: ARG001
    """Handle the ``fields`` command."""
    return _dump(client.fields())


_DISPATCH: dict[str, Callable[[GleifClient, argparse.Namespace], str]] = {
    "get": _cmd_get,
    "search": _cmd_search,
    "owners": _cmd_owners,
    "children": _cmd_children,
    "isins": _cmd_isins,
    "fuzzy": _cmd_fuzzy,
    "fields": _cmd_fields,
}


def _run(client: GleifClient, args: argparse.Namespace) -> str:
    """Dispatch a parsed command to the v2 client and return output text."""
    return _DISPATCH[args.command](client, args)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI. Returns a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    client = GleifClient()
    try:
        output = _run(client, args)
    except PyGLEIFError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 1
    sys.stdout.write(f"{output}\n")
    return 0


def _entrypoint() -> None:
    """Console entrypoint that propagates the exit code."""
    raise SystemExit(main())


if __name__ == "__main__":
    _entrypoint()
