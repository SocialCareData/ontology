"""Validate examples/ against the SHACL shapes.

examples/<standard>[/<profile>]/ mirrors the standards: records are checked
against <standard>/<standard>-<profile or "standard">-shape.ttl.
valid-*.jsonld must conform, invalid-*.jsonld must not.

Each folder's expectations.json also pins the violations every invalid record
must produce - focus type, property and constraint, named through the module
context - so an invalid example cannot start failing for the wrong reason, or
for more reasons than intended, without someone noticing.

    python .github/scripts/validate_examples.py           # check
    python .github/scripts/validate_examples.py --update  # rewrite expectations.json
"""

import argparse
import json
import sys
from pathlib import Path

from pyshacl import validate
from rdflib import RDF, SH, Graph, URIRef
from rdflib.plugins.shared.jsonld.context import Context

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples"
EXPECTATIONS = "expectations.json"


def shapes_for(example_dir: Path) -> Graph:
    parts = example_dir.relative_to(EXAMPLES).parts
    standard = parts[0]
    profile = parts[1] if len(parts) > 1 else "standard"
    std_dir = ROOT / standard
    main = std_dir / f"{standard}-{profile}-shape.ttl"
    print(f"Using main shape file: {main.relative_to(ROOT)}")
    if not main.is_file():
        raise FileNotFoundError(f"no shape file {main.relative_to(ROOT)}")
    return Graph().parse(main, format="turtle")


def module_context(standard: str) -> dict:
    return json.loads((ROOT / standard / "context.jsonld").read_text())["@context"]


def load_example(path: Path, context: dict) -> Graph:
    # Swap the released context for the local module context matching the shapes,
    # so validation needs no network and tests this commit's context.
    data = json.loads(path.read_text())
    data["@context"] = context
    return Graph().parse(data=json.dumps(data), format="json-ld")


def constraint_name(component: URIRef) -> str:
    """sh:MinCountConstraintComponent -> sh:minCount, the term a shape author writes."""
    local = str(component).removeprefix(str(SH)).removesuffix("ConstraintComponent")
    return "sh:" + (local.lower() if local.isupper() else local[0].lower() + local[1:])


def term_names(raw: dict, context: Context) -> dict[str, str]:
    """IRI -> the context term a record writes for it.

    Walks type- and property-scoped contexts too (an Organisation's `name` is
    sg:entityName), with top-level terms taking precedence. rdflib's own
    to_symbol() misses scoped terms and terms that carry type coercion.
    """
    names: dict[str, str] = {}
    pending = [raw]
    while pending:
        scope = pending.pop(0)
        for name, definition in scope.items():
            if name.startswith("@") or ":" in name:
                continue
            iri = definition if isinstance(definition, str) else (definition or {}).get("@id")
            if isinstance(iri, str) and not iri.startswith("@"):
                names.setdefault(context.expand(iri) or iri, name)
            if isinstance(definition, dict) and isinstance(definition.get("@context"), dict):
                pending.append(definition["@context"])
    return names


def violations(report: Graph, data: Graph, names: dict[str, str], context: Context) -> list[dict]:
    """The report's violations as {focus, path, constraint}, in the record's own terms."""

    def term(node) -> str:
        if not isinstance(node, URIRef):
            return "(anonymous)"
        return names.get(str(node)) or context.to_symbol(str(node))

    found = []
    for result in report.subjects(RDF.type, SH.ValidationResult):
        if report.value(result, SH.resultSeverity) != SH.Violation:
            continue
        entry = {}
        focus = report.value(result, SH.focusNode)
        types = sorted(term(t) for t in data.objects(focus, RDF.type))
        if types:
            entry["focus"] = " ".join(types)
        path = report.value(result, SH.resultPath)
        if path is not None:
            entry["path"] = term(path)
        entry["constraint"] = constraint_name(report.value(result, SH.sourceConstraintComponent))
        found.append(entry)
    return sorted(found, key=lambda e: (e.get("focus", ""), e.get("path", ""), e["constraint"]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--update", action="store_true",
                        help=f"rewrite each folder's {EXPECTATIONS} from the current shapes")
    args = parser.parse_args()

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
        raw_context = module_context(rel_dir.parts[0])
        context = Context(raw_context)
        names = term_names(raw_context, context)
        expectations_file = example_dir / EXPECTATIONS
        pinned = {} if args.update or not expectations_file.is_file() \
            else json.loads(expectations_file.read_text())
        produced = {}

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
                data = load_example(path, raw_context)
                conforms, report_graph, report = validate(
                    data,
                    shacl_graph=shapes,
                    inference="none",
                )
            except Exception as e:
                print(f"::error file={rel}::{rel}: could not validate: {e}")
                failures += 1
                continue
            if conforms != expected:
                failures += 1
                want = "conform" if expected else "fail validation"
                print(f"FAIL  {rel}")
                print(f"::error file={rel}::{rel}: expected to {want}")
                if not conforms:
                    print(f"::group::Validation report for {rel}")
                    print(report)
                    print("::endgroup::")
                continue
            if expected:
                print(f"ok    {rel}")
                continue

            actual = violations(report_graph, data, names, context)
            produced[path.name] = actual
            if args.update:
                print(f"ok    {rel}")
            elif path.name not in pinned:
                failures += 1
                print(f"FAIL  {rel}")
                print(f"::error file={rel}::{rel}: not in {rel_dir}/{EXPECTATIONS}; "
                      "run with --update and review the diff")
            elif pinned[path.name] != actual:
                failures += 1
                print(f"FAIL  {rel}")
                print(f"::error file={rel}::{rel}: violations differ from {rel_dir}/{EXPECTATIONS}")
                print(f"::group::Expected and actual violations for {rel}")
                print("expected:", json.dumps(pinned[path.name], indent=2))
                print("actual:  ", json.dumps(actual, indent=2))
                print("::endgroup::")
            else:
                print(f"ok    {rel}")

        if args.update:
            if produced:
                expectations_file.write_text(json.dumps(produced, indent=2) + "\n")
                print(f"wrote {expectations_file.relative_to(ROOT)}")
            elif expectations_file.is_file():
                expectations_file.unlink()
                print(f"removed {expectations_file.relative_to(ROOT)}")
        else:
            for stale in sorted(set(pinned) - set(produced)):
                if not (example_dir / stale).is_file():
                    failures += 1
                    print(f"::error file={expectations_file.relative_to(ROOT)}::"
                          f"{stale} is pinned but no such example exists")

    print(f"\n{checked} examples checked, {failures} problem(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
