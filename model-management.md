# Managing the data models — LinkML & SHACL validation

Every data standard under `src/_data/model/<standard>/` is defined as a
[LinkML](https://linkml.io/) schema, which is the **authoritative source** for
that model. From one YAML file the SHACL shapes, OWL/RDF, JSON Schema, Pydantic
classes and documentation are all *generated*.

> ⚠️ **Do not edit the generated artifacts** (`*-shape.ttl`, `*.ttl` ontology,
> JSON Schema, docs). Edit the LinkML `*.yaml` and regenerate — any manual edits
> to generated files are overwritten.

This guide covers the LinkML → SHACL workflow that is common to **all** models.
Each model's own `README.md` describes only what is specific to that model
(its classes, profiles, cardinalities).

## Module layout and the single MAIS ontology

The models are authored as **independently-versioned modules** — one folder each
under `src/_data/model/` — that compose into one **Social Care MAIS** ontology:

- `common/` — shared building blocks (`Identifier`, `Name`, `Address`, `Contact`
  and their vocabularies), depended on by the domain modules.
- `person/`, `placements/`, `safeguarding/`, `assessments-and-plans/` — the
  domain standards; each imports `common` for the shared objects.
- `mais/mais.yaml` — the **umbrella** schema. It has no terms of its own; it
  `imports` every module so the merged ontology can be generated from one file.
  `mais/manifest.yml` pins the module versions that make up a release.

Everything lives under a **single flat namespace**,
`https://ontology.socialcaredata.io/`, so a term keeps the same IRI whether used
in a module or in the merged ontology. Same-named slots across modules therefore
share one IRI — keep genuinely different fields distinctly named (e.g.
`specialCommunicationNeeds`, `serviceFrequency`, `measurementValue`).

Cross-module imports use each module's ontology id (e.g.
`https://ontology.socialcaredata.io/common`) and are resolved to local files by
the single top-level `imports.json`. **Importmap paths are resolved relative to
the importing file**, so they are written `../<module>/<file>` and generators
are run from the module's own directory:

```bash
# a module (references common via the shared importmap)
cd safeguarding && gen-owl --no-mergeimports -im ../imports.json safeguarding-standard.yaml

# the whole merged MAIS ontology
cd mais && gen-owl --mergeimports -im ../imports.json mais.yaml > social-care-mais.ttl
```

The `{% schema_table %}` generator finds this map by walking up from the schema's
own directory to the repository root, so a module never needs its own copy. A
module *may* still place an `imports.json` beside its schemas to override
individual ids — entries nearer the schema win, and the rest of the shared map
still applies — but `gen-owl` / `gen-shacl` see only the one map passed to `-im`,
so keep the top-level map authoritative. An import that resolves to no file is an
error in both tools rather than a silent skip.

## Prerequisites

```bash
pip install linkml   # provides gen-shacl, gen-owl, gen-json-schema, gen-doc, …
```

LinkML needs Python ≥ 3.11 with the `_lzma` stdlib module (some pyenv builds of
3.13/3.14 ship without it — use a 3.11 interpreter if `gen-shacl` fails to
import `_lzma`).

## Anatomy of a LinkML model

| Element | Purpose | Becomes (in SHACL) |
| --- | --- | --- |
| **classes** | entities (a root class + sub-entities) | one `NodeShape` per class (`--suffix Shape` → `pl:PlacementShape`) |
| **slots** | properties | `sh:property` blocks (`sh:minCount`/`sh:maxCount` from `required`/`multivalued`, `sh:pattern`, `sh:minInclusive`/`sh:maxInclusive` from `minimum_value`/`maximum_value`) |
| **enums** | controlled vocabularies | `sh:in ( … )` of concept IRIs |
| **types** | custom datatypes | `sh:datatype` (e.g. `nonNegativeInteger` → `xsd:nonNegativeInteger`) |
| **mixins** | a block of slots shared by several classes | the inherited `sh:property` blocks, repeated in each class's own `NodeShape` |

- **Object references** (e.g. `placementAvailability`, `actualPlacement`) are
  modelled as **class-ranged slots** → `sh:class` + `sh:nodeKind sh:BlankNodeOrIRI`.
- **URI-valued** scalars use `range: uri` → `sh:nodeKind sh:IRI` (needed when the
  value is an `@id` node rather than a literal).
- **Mixins** avoid repeating a shared block of slots on every class that carries
  it (assessments-and-plans does this with `FoundationalInformation`). The
  generators resolve them, and so does `{% schema_table %}`, which lists a class's
  inherited slots before its own. One caveat: do **not** narrow an inherited slot
  with `slot_usage` unless the class also declares that slot itself, or the
  `slot_usage` block repeats `range:` — `gen-owl` otherwise derives an induced
  slot that falls back to `default_range` and emits an `owl:allValuesFrom
  xsd:string` axiom contradicting the slot's real range.

### Controlled vocabularies: code, label, meaning

Model an enum so each permissible value carries the three things a vocabulary
needs — its data **code**, a human **label**, and the concept **IRI**:

```yaml
enums:
  PlacementUrgency:
    title: Placement Urgency          # taxonomy title
    permissible_values:
      "Within 5 days":                # KEY = the code (the value used in data)
        title: Within 5 days          # human label
        meaning: pu:WithinFiveDays    # concept IRI -> used in SHACL sh:in
        description: Placement is needed within five days.
```

- The **key** is the value's code (the SKOS-style *notation*). Quote it when it
  contains spaces or is bool-like (`"No"`, `"Within 5 days"`, `"-8"`).
- `meaning` (not the key) is what `gen-shacl` puts in `sh:in`, so renaming keys
  never changes the generated shape.
- The schema-table docs render these as a `Code | Label | Definition` table
  (see `src/assets/js/schema-table/`).

## Regenerating downstream artifacts

> **Normally you don't.** The published `.ttl` artifacts are built by
> [`build_ontology.py`](../../assets/scripts/build_ontology.py) and synced to
> [SocialCareData/ontology](https://github.com/SocialCareData/ontology) by the
> `Sync ontology` workflow. Run the script rather than the raw commands, so you
> get the same bytes CI does:
>
> ```bash
> pip install -r src/assets/scripts/requirements.txt
> python src/assets/scripts/build_ontology.py --out build/ontology
> ```
>
> The commands below are what that script runs, for when you need to inspect a
> single schema by hand.

Run from the model's directory. Using placements as the example:

```bash
# SHACL — one shape per class
gen-shacl --non-closed --suffix Shape -im ../imports.json placements-standard.yaml > placements-standard-shape.ttl

# OWL / RDF, JSON Schema, docs, Pydantic, …
gen-owl --no-mergeimports --ontology-uri-suffix '' --consolidate-cardinality-axioms --skip-vacuous-min-zero-cardinality-axioms --skip-vacuous-local-range-axioms -im ../imports.json placements-standard.yaml > placements-standard.ttl
gen-json-schema -im ../imports.json placements-standard.yaml
gen-doc -im ../imports.json placements-standard.yaml
```

`--non-closed` produces open shapes and `--suffix Shape` names them
`…Shape` — both keep the output aligned with any hand-written shapes.
`-im ../imports.json` resolves each cross-module import (e.g.
`https://ontology.socialcaredata.io/common`) to its local file; the path is
`../` because the single importmap sits one level above the module directories.
`gen-shacl` keeps `--include-imports` (the default) so the shared-object shapes
are emitted and validate the nested objects; `gen-owl` uses `--no-mergeimports`
so the imported module's classes are referenced via `owl:imports` rather than
copied in.

`--ontology-uri-suffix ''` is **not** optional. Left off, `gen-owl` appends its
default `.owl.ttl`, so a schema declaring
`id: https://ontology.socialcaredata.io/placements` publishes itself as
`…/placements.owl.ttl` and is not dereferenceable at its own IRI. (The older
artifacts under `src/assets/model/` predate this and still carry the bug.) Where
several files share one `id` — placements keeps frozen v1 and v0.1 alongside the
current schema — the build gives the frozen ones a version-qualified suffix
(`--ontology-uri-suffix /1.0.0`) so no two published files claim the same
`owl:Ontology` IRI.

### The output is not byte-reproducible on its own

Two identical `gen-owl` or `gen-shacl` runs emit **isomorphic but differently
ordered** Turtle — rdflib's blank-node labelling varies per process, and
`PYTHONHASHSEED` does not affect it. Published directly, that would open a large
and meaningless pull request on every sync. `build_ontology.py` therefore
canonicalises every file (RDFC-1.0 blank-node relabelling, then re-serialise)
before writing it, and CI re-runs the whole build and diffs the two trees to
keep the guarantee honest. If you compare a hand-run artifact against a
published one, compare the graphs, not the bytes.

## What `gen-shacl` does NOT generate

`gen-shacl` (verified with LinkML 1.11.1) **ignores conditional logic**:

- class-level `rules:` (if/then `preconditions`/`postconditions`), and
- class-level boolean expressions (`none_of` / `any_of` / `all_of`).

These remain the semantic source of truth (honoured by `linkml-validate` and the
Python/Pydantic artifacts), but they produce **no** SHACL. To enforce such a
constraint in SHACL, hand-maintain the equivalent shape in a separate
`*-rules-shape.ttl` and load it *alongside* the generated shape — the validator
accepts a list of shape files per profile (see below).

Placements does this for its four "Other ⇒ free-text required" rules in
[`placements/placements-base-rules-shape.ttl`](placements/placements-base-rules-shape.ttl),
e.g.:

```turtle
pl:CulturalNeedsOtherCheckShape a sh:NodeShape ;
    sh:targetClass pl:PlacementRequirements ;
    sh:not [
        sh:property [ sh:path pl:culturalNeeds ; sh:hasValue cln:Other ] ;
        sh:property [ sh:path pl:culturalNeedsOther ; sh:maxCount 0 ]
    ] .
```

Keep the rules-shape in sync with the schema's `rules:` blocks by hand.

> **`@type: @vocab` in `context.jsonld`.** For a controlled-vocabulary property
> to be validated at all, its JSON-LD context entry must serialise the value to
> the concept IRI. Use `"@type": "@vocab"` (with the enum's `@vocab` base), not
> `"@type": "@id"` — the latter drops the value entirely.

## One model, several shapes (profiles)

When cardinalities differ by context (e.g. the same class is stricter in one
scenario than another), split the model into a **shared core** plus **profile**
schemas that `import` it and redefine the root class:

- the core defines the sub-entities, slots and vocabularies once;
- each profile fully redefines the root class with its own cardinalities
  (LinkML *replaces* an imported class rather than merging it, so list all its
  slots);
- generate SHACL from **each profile file separately** — every profile emits its
  own root-class shape plus the identical shared sub-entity shapes.

The Person model uses this (`person-standard.yaml` core +
`person-subject-of-care.yaml` / `person-connected.yaml`); see
[`person/README.md`](person/README.md). The profiles import the core by its
ontology id (`https://ontology.socialcaredata.io/person`), resolved through the
same top-level `imports.json` as every other cross-module import.

## Validating the examples

Each model ships JSON-LD examples that are checked against its generated shapes
by the standard-agnostic validator in
[`src/assets/shacl/validation/`](../shacl/validation/README.md). Files named
`valid-*.jsonld` must conform; `invalid-*.jsonld` must not.

```bash
cd src/assets/shacl/validation
npm install
node validate.js                          # every standard, every profile
node validate.js placements               # one standard
node validate.js person subject-of-care   # one standard, one profile
```

A profile may load **several** shape files (the generated shape plus any
hand-maintained `*-rules-shape.ttl`); they are merged before validation.
Register a new standard/profile in the `STANDARDS` map at the top of
`validate.js`.
