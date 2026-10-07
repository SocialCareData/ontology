"""Validate examples/ against the SHACL shapes.

examples/<standard>[/<profile>]/ mirrors the standards: records are checked
against <standard>/<standard>-<profile or "standard">-shape.ttl plus any
<standard>/*-rules-shape.ttl. valid-*.jsonld must conform, invalid-*.jsonld
must not.
"""

import json
import sys
from pathlib import Path

from pyshacl import validate
from rdflib import Graph

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples"


def shapes_for(example_dir: Path) -> Graph:
    parts = example_dir.relative_to(EXAMPLES).parts
    standard = parts[0]
    profile = parts[1] if len(parts) > 1 else "standard"
    std_dir = ROOT / standard
    main = std_dir / f"{standard}-{profile}-shape.ttl"
    print(f"Using main shape file: {main.relative_to(ROOT)}")
    if not main.is_file():
        raise FileNotFoundError(f"no shape file {main.relative_to(ROOT)}")
    graph = Graph()
    for f in [main, *sorted(std_dir.glob("*-rules-shape.ttl"))]:
        graph.parse(f, format="turtle")
    return graph


def load_example(path: Path, standard: str) -> Graph:
    # Swap the released context for the local module context matching the shapes,
    # so validation needs no network and tests this commit's context.
    data = json.loads(path.read_text())
    context = json.loads((ROOT / standard / "context.jsonld").read_text())
    data["@context"] = context["@context"]
    return Graph().parse(data=json.dumps(data), format="json-ld")


def main() -> int:
    failures = 0
    checked = 0
    dirs = sorted({p.parent for p in EXAMPLES.rglob("*.jsonld")})
    for example_dir in dirs:
        rel_dir = example_dir.relative_to(EXAMPLES)
        try:
            shapes = shapes_for(example_dir)
        except FileNotFoundError as e:
            print(f"::error::{rel_dir}: {e}")
            failures += 1
            continue
        for path in sorted(example_dir.glob("*.jsonld")):
            rel = path.relative_to(ROOT)
            if path.name.startswith("valid-"):
                expected = True
            elif path.name.startswith("invalid-"):
                expected = False
            else:
                print(f"::error file={rel}::{rel}: name must start with valid- or invalid-")
                failures += 1
                continue
            checked += 1
            try:
                conforms, _, report = validate(
                    load_example(path, rel_dir.parts[0]),
                    shacl_graph=shapes,
                    inference="none",
                )
            except Exception as e:
                print(f"::error file={rel}::{rel}: could not validate: {e}")
                failures += 1
                continue
            if conforms == expected:
                print(f"ok    {rel}")
            else:
                failures += 1
                want = "conform" if expected else "fail validation"
                print(f"FAIL  {rel}")
                print(f"::error file={rel}::{rel}: expected to {want}")
                if not conforms:
                    print(f"::group::Validation report for {rel}")
                    print(report)
                    print("::endgroup::")
    print(f"\n{checked} examples checked, {failures} problem(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
