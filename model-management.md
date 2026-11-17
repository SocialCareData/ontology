# Data models

Each data standard is a [LinkML](https://linkml.io/) schema under
`src/_data/model/<module>/`. The LinkML YAML is the **single source of truth**.
The OWL ontologies and SHACL shapes are generated from it automatically and
published to [SocialCareData/ontology](https://github.com/SocialCareData/ontology);
they are not kept in this repository. The JSON-LD contexts are generated from it
too, but are committed here (see [JSON-LD contexts](#json-ld-contexts)).

| Repository | Holds |
| --- | --- |
| this one | LinkML schemas, generated JSON-LD contexts, JSON-LD examples, release manifest |
| [SocialCareData/ontology](https://github.com/SocialCareData/ontology) | generated OWL (`*.ttl`) and SHACL (`*-shape.ttl`), and a copy of the contexts |

Each module's own `README.md` covers what is specific to that module.

## Layout

```text
src/_data/model/
├── common/                 shared objects: Identifier, Name, Address, Contact
├── person/                 domain modules, each importing common
├── placements/
├── safeguarding/
├── assessments-and-plans/
├── examples/               valid and invalid JSON-LD records, one folder per module (and profile)
├── social-care.yaml        umbrella schema: imports every module, no terms of its own
├── manifest.yaml           module versions that make up an ontology release
├── context.jsonld          references every module's JSON-LD context (maintained by hand)
└── imports.json            maps module IRIs to local files for the LinkML tools
```

Modules are versioned independently, but every term lives in one flat namespace,
`https://ns.socialcaredata.io/`. A slot name therefore means the same thing in
every module: give genuinely different fields distinct names, and move fields
that really are shared into `common`. CI checks this on every pull request.

## LinkML basics

See the [LinkML documentation](https://linkml.io/linkml/) for details. In short:

| LinkML | Purpose | Becomes in SHACL |
| --- | --- | --- |
| **classes** | entities | a `NodeShape` per class |
| **slots** | properties | `sh:property` (cardinality from `required` / `multivalued`) |
| **enums** | controlled vocabularies | `sh:in ( … )` of concept IRIs |
| **types** | custom datatypes | `sh:datatype` |
| **mixins** | slots shared by several classes | the inherited `sh:property` blocks |

A slot whose `range` is a class references another object; `range: uri` holds an IRI.

### Controlled vocabularies

Each permissible value carries a **code** (the key, used in data), a **label**
(`title`) and a concept **IRI** (`meaning`, which is what SHACL checks):

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

Quote keys that contain spaces or look like booleans or numbers (`"No"`, `"-8"`).
The generated JSON-LD context expands each code, its `title` and the concept's
local name (`WithinFiveDays`) to the concept IRI, so SHACL can validate the value.
To accept another spelling as well, list it under `aliases`:

```yaml
      "Risk present":
        title: Risk present
        meaning: rl:RiskPresent
        aliases: ["Risk Present"]       # also accepted in data
```

Codes and aliases must be unique within the enum, and must not contain `:` or `/`
(JSON-LD would read them as IRIs).

### Pattern messages

A failed `pattern` is hard to explain from the regex alone. Give the slot an
`sh:message` annotation saying what a valid value looks like, and the validator
shows it under the error:

```yaml
prefixes:
  sh: http://www.w3.org/ns/shacl#

slots:
  postcode:
    pattern: "^[A-Z]{1,2}[0-9][0-9A-Z]? ?[0-9][A-Z]{2}$"
    annotations:
      sh:message: "Use a UK postcode in upper case, with an optional space - for example `AB1 2CD`."
```

Write a whole sentence; `` `code` `` and `**bold**` are rendered. The message
lands on the slot's property shape, so other SHACL tools show it for any failure
on that slot, not only the pattern. Keep `:` out of the text: LinkML reads such
a value as a CURIE, and gen-shacl fails with "does not look like a valid URI".

### Profiles

When one class needs different cardinalities in different contexts, a **core**
schema defines everything once and **profile** schemas import it and redefine the
root class. Person does this; see [person/README.md](person/README.md).

## JSON-LD contexts

Each module's `context.jsonld` is **generated** from the LinkML YAML by
[`build_contexts.py`](../../assets/scripts/build_contexts.py). Don't edit them
by hand: change the schema and regenerate. CI fails a pull request whose
committed contexts differ from the generated ones. The root `context.jsonld` is
not generated: it is maintained by hand and only lists references to the module
contexts.

```bash
pip install -r src/assets/scripts/requirements.txt
python src/assets/scripts/build_contexts.py            # regenerate every context
python src/assets/scripts/build_contexts.py --check    # what CI runs: fail, with a diff, if any is stale
```

How the schema maps to the context:

| In the schema | In the context |
| --- | --- |
| slot `title` (or the slot name if it has none) | the JSON key records use. The slot name is accepted too |
| `slot_uri` | the property IRI (`@id`) |
| `range:` a class, or `uri` | `"@type": "@id"` |
| `range:` date, datetime, boolean, decimal, integer | coerced to that XSD datatype |
| `range: Any` (e.g. a FHIR Timing) | `"@type": "@json"`: kept whole as a JSON literal |
| `multivalued: true` | `"@container": "@set"` |
| `range:` an enum | `"@type": "@vocab"`: each code, title, concept local name and alias expands to the `meaning` IRI |
| one JSON key used for different slots on different classes (`name` on a Person and on a Contact) | defined in a type-scoped context on each class, so records must give those objects an `@type` |

A module's context covers everything it imports, so each is self-contained. For
`person` it is generated from the core `person-standard.yaml`, which the profiles share.

The `@context` written in the example records is not used for validation: both
`validate_examples.py` and the browser validator replace it with the module
context.

## CSV metadata

Some standards are also exchanged as a flat CSV whose columns we do not
control, such as the Placements return. For a module that maps its slots to CSV
columns, [`build_csvw.py`](../../assets/scripts/build_csvw.py) generates a
[CSVW](https://www.w3.org/TR/tabular-metadata/) `csv-metadata.json` beside its
`context.jsonld`. It says how each row becomes the same RDF a JSON-LD record
would, so a CSV file is checked against the same SHACL shapes. Like the
contexts, it is generated: change the schema and regenerate, and CI fails a pull
request whose committed metadata is stale. It is published to
SocialCareData/ontology with the shapes.

```bash
# regenerate
python src/assets/scripts/build_csvw.py
# what CI runs
python src/assets/scripts/build_csvw.py --check
```

The mapping is written as annotations, each named after the CSVW property it
becomes. The schema declares the `csvw:` and `dsv:` prefixes.

| Annotation | On | Meaning |
| --- | --- | --- |
| `csvw:titles: <column>` | slot | The column that holds the slot. A module gets metadata once any slot has one. |
| `csvw:format` | slot | The cell format, when the default will not do. Booleans default to `"Yes\|No"` (the true value first), so `"No\|Yes"` maps a question that is the negation of the slot. A date takes a pattern such as `"dd/MM/yyyy"`. |
| `dsv:headerMatch: first-line` | schema | Header cells hold the column name on their first line, followed by help text. |
| `csvw:null: N/A` | schema | A token meaning "no value". `""` always means no value. A column whose enum has a value written this way keeps it as that value. |
| `csvw:separator: ","` | schema | Separates the values of a multivalued slot within a cell. |
| `csvw:titles` | permissible value | Another spelling the CSV uses for the value, for a spelling that cannot be an `alias` because it is not a valid JSON-LD term, such as `N/A`. It is also the label the validator shows for the value. |

How the schema maps to the metadata:

- **Rows and nested objects.** Each row is one record of the `tree_root` class.
  The objects it links to through class-ranged slots become nodes of that row.
  An optional object whose columns are all empty is left out, rather than
  reported as incomplete.
- **Enum columns.** These accept the code, title, aliases, concept local name and
  `csvw:titles` of each value, ignoring case and spaces: `<5 days` is
  `< 5 days`. Prefer adding an `alias` for a spelling the CSV uses, because
  JSON-LD records then accept it too.
- **Not copied to the published artifacts.** `build_ontology.py` drops the
  `csvw:` and `dsv:` annotations from the published OWL and SHACL. They describe
  the CSV, not the ontology.

The validator reads CSV with this metadata (`--csv-metadata`). See its
[CSV documentation](https://theodi.github.io/data-standard-validator/csv/) for
the CSVW it supports.

## Generating the ontology and shapes

**Automatically.** On every push to `main` that changes the models, the
`Sync ontology` workflow runs
[`build_ontology.py`](../../assets/scripts/build_ontology.py) and opens a pull
request on [SocialCareData/ontology](https://github.com/SocialCareData/ontology)
with:

- `<module>/<schema>.ttl` (OWL) and `<module>/<schema>-shape.ttl` (SHACL) for every schema;
- `social-care.ttl` at the root, which `owl:imports` each module at the version
  pinned in `manifest.yaml`;
- `social-care-shape.ttl` at the root, with every module's shapes merged into one file.

To cut a release, update the module versions and `ontology_version` in
`manifest.yaml`. `social-care.yaml` declares no version: the build gives it
`ontology_version`.

**Manually.** Requires Python ≥ 3.11. To reproduce the published output:

```bash
pip install -r src/assets/scripts/requirements.txt
python src/assets/scripts/build_ontology.py --out build/ontology
```

To inspect a single schema, run the generators from its module directory.
`-im ../imports.json` resolves cross-module imports to the local files:

```bash
cd src/_data/model/placements
gen-shacl --non-closed --suffix Shape --include-annotations -im ../imports.json placements-standard.yaml > placements-standard-shape.ttl
gen-owl --no-mergeimports --ontology-uri-suffix '' --consolidate-cardinality-axioms --skip-vacuous-min-zero-cardinality-axioms --skip-vacuous-local-range-axioms -im ../imports.json placements-standard.yaml > placements-standard.ttl
```

### What gen-shacl does not generate

`gen-shacl` ignores class-level `rules:` and `any_of` / `all_of` / `none_of`.
These still apply when validating with LinkML, but to enforce them in SHACL write
the equivalent shape by hand in a `*-rules-shape.ttl` and load it alongside the
generated shape.

## Validation

The [examples](https://github.com/SocialCareData/standard/tree/main/src/_data/model/examples)
are organised as `examples/<module>[/<profile>]/`. `valid-*.jsonld` must conform
and `invalid-*.jsonld` must not, and each folder's `expectations.json` pins the
violations every invalid record must produce. CI checks them on every pull
request, against shapes built from that commit's schemas:

```bash
pip install -r src/assets/scripts/requirements.txt
python src/assets/scripts/validate_examples.py            # check
python src/assets/scripts/validate_examples.py --update   # rewrite expectations.json, then review the diff
```

`valid-*.csv` and `invalid-*.csv` follow the same rules. They are read through the
module's `csv-metadata.json` by the installed `data-standard-validator`
command. If it is not installed, the script installs the latest release with
`npm install -g @theodi/data-standard-validator@latest`, so checking the
examples also needs Node.js 22 or later. CI installs the latest release before
every run. Their expectations are pinned as the row, column and issue code a
CSV author sees.

To validate your own data, use
[@theodi/data-standard-validator](https://www.npmjs.com/package/@theodi/data-standard-validator) with the
published shape for the standard:

```bash
npx @theodi/data-standard-validator -s https://raw.githubusercontent.com/SocialCareData/ontology/main/placements/placements-standard-shape.ttl yourdata.jsonld
```

The shapes for every standard are published to
[SocialCareData/ontology](https://github.com/SocialCareData/ontology), as
`<module>/<module>-standard-shape.ttl`.

Or use the browser version at <https://standard.socialcaredata.io/validator>.
It fetches shapes and contexts from
[SocialCareData/ontology](https://github.com/SocialCareData/ontology), so it always
checks against the published artifacts, and offers the `valid-*` examples from
this repository. To add a standard or profile to the browser version, add it to
[`src/_data/validator.yml`](https://github.com/SocialCareData/standard/blob/main/src/_data/validator.yml).
