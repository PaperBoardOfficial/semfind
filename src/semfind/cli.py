"""CLI entry point for semfind."""

import argparse
import sys

from . import __version__
from .index import DEFAULT_MODEL
from .search import search


# ANSI color helpers
def _cyan(s: str) -> str:
    return f"\033[36m{s}\033[0m"


def _green(s: str) -> str:
    return f"\033[32m{s}\033[0m"


def _dim(s: str) -> str:
    return f"\033[2m{s}\033[0m"


def _read_context_lines(filepath: str) -> list[str]:
    with open(filepath) as f:
        return f.readlines()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="semfind",
        description="Semantic grep — search files by meaning, not pattern.",
    )
    parser.add_argument("query", help="Search query")
    parser.add_argument("files", nargs="+", help="Files to search")
    parser.add_argument("-k", "--top-k", type=int, default=5, help="Number of results (default: 5)")
    parser.add_argument("-n", "--context", type=int, default=0, help="Lines of context before/after match")
    parser.add_argument("-m", "--max-distance", type=float, default=None, help="Minimum similarity threshold")
    parser.add_argument("--reindex", action="store_true", help="Force re-embed even if cache exists")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Embedding model (default: {DEFAULT_MODEL})")
    parser.add_argument("--no-cache", action="store_true", help="Don't save/load embeddings cache")
    parser.add_argument("--version", action="version", version=f"semfind {__version__}")

    args = parser.parse_args(argv)

    # Validate files exist
    missing = [f for f in args.files if not __import__("os").path.isfile(f)]
    if missing:
        for f in missing:
            print(f"semfind: {f}: No such file", file=sys.stderr)
        return 1

    results = search(
        query=args.query,
        filepaths=args.files,
        top_k=args.top_k,
        max_distance=args.max_distance,
        model_name=args.model,
        reindex=args.reindex,
        no_cache=args.no_cache,
    )

    if not results:
        print("No results found.", file=sys.stderr)
        return 0

    # Cache of file lines for context display
    file_lines: dict[str, list[str]] = {}
    ctx = args.context

    for r in results:
        if ctx > 0 and r.file not in file_lines:
            file_lines[r.file] = _read_context_lines(r.file)

        if ctx > 0:
            lines = file_lines[r.file]
            start = max(0, r.line_num - 1 - ctx)
            end = min(len(lines), r.line_num + ctx)
            for i in range(start, end):
                ln = i + 1
                text = lines[i].rstrip("\n")
                if ln == r.line_num:
                    print(f"{_cyan(r.file)}:{_green(str(ln))}: {text}  {_dim(f'({r.score:.3f})')}")
                else:
                    print(f"{_dim(f'{r.file}:{ln}: {text}')}")
            if r != results[-1]:
                print("--")
        else:
            print(f"{_cyan(r.file)}:{_green(str(r.line_num))}: {r.text}  {_dim(f'({r.score:.3f})')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
