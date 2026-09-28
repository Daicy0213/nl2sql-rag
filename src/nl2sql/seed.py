from __future__ import annotations

import argparse
from nl2sql.demo_data import seed_demo


def seed(*, reset: bool = False) -> None:
    """Load the expanded deterministic commerce dataset."""
    counts = seed_demo(reset=reset)
    summary = ", ".join(f"{name}={count}" for name, count in counts.items())
    print(f"Expanded seed ready: {summary}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load deterministic NL2SQL demo data")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="explicitly replace an older generated analytics dataset",
    )
    seed(reset=parser.parse_args().reset)
