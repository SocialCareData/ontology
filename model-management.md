# Data models

Each data standard is a [LinkML](https://linkml.io/) schema under
`src/_data/model/<module>/`. The LinkML YAML is the **single source of truth**.
The OWL ontologies and SHACL shapes are generated from it automatically and
published to [SocialCareData/ontology](https://github.com/SocialCareData/ontology);
they are not kept in this repository.

| Repository | Holds |
| --- | --- |
| this one | LinkML schemas, JSON-LD contexts, JSON-LD examples, release manifest |
| [SocialCareData/ontology](https://github.com/SocialCareData/ontology) | generated OWL (`*.ttl`) and SHACL (`*-shape.ttl`) |
| [SocialCareData/validator](https://github.com/SocialCareData/validator) | the validator that checks data against those shapes |

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
├── context.jsonld          all module JSON-LD contexts combined
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
In `context.jsonld`, map vocabulary properties with `"@type": "@vocab"` so their
values expand to the concept IRI and can be validated.

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

To validate your own data, use the
[validator](https://github.com/SocialCareData/validator):

```bash
npx @socialcaredata/validator -p placements yourdata.jsonld
npx @socialcaredata/validator profiles   # list the available profiles
```

Or use the browser version at <https://socialcaredata.github.io/validator/>.
The validator fetches shapes and contexts from
[SocialCareData/ontology](https://github.com/SocialCareData/ontology), so it always
checks against the published artifacts, and offers the `valid-*` examples from
this repository. To add a standard or profile, see the validator's
[contributing guide](https://github.com/SocialCareData/validator/blob/main/docs/contributing.md).
