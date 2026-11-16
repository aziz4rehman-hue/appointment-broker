"""CLI. Repeated --eval calls share one calendar."""

from __future__ import annotations

import argparse

from apptbroker import __version__
from apptbroker.agents import AppointmentBroker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="apptbroker",
        description="AI appointment broker. Holds a slot, then confirms it. No network.",
    )
    parser.add_argument("--version", action="version", version=f"apptbroker {__version__}")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--eval", action="append", default=[])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    broker = AppointmentBroker()
    if args.demo:
        print(broker.demo())
        return 0
    if not args.eval:
        build_parser().print_help()
        return 0
    blocks = [f"> {command}\n{broker.handle(command)}" for command in args.eval]
    print("\n".join(blocks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
