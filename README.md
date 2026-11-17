# Social Care MAIS ontology

OWL/RDF ontologies, SHACL shapes, JSON-LD contexts and example records for the
Social Care MAIS (Multi-Agency Information Sharing) data standards, published
under the single flat namespace `https://ns.socialcaredata.io/`.

> ## Everything here is generated — do not edit
>
> These files are produced from the LinkML schemas and examples in
> [SocialCareData/standard](https://github.com/SocialCareData/standard) under
> `src/_data/model/`, and are overwritten on every sync. Edit the source there
> and let the sync republish; changes made directly in this repository will be
> silently reverted.

## Layout

One directory per module, mirroring the source tree. Each LinkML schema yields
an ontology (`<name>.ttl`) and, where applicable, a SHACL shape
(`<name>-shape.ttl`). Every module also ships a `context.jsonld`, and modules
with a tabular CSV form ship a CSVW `csv-metadata.json` beside it.

| Path | Contents |
| --- | --- |
| `common/` | Shared building blocks — `Identifier`, `Name`, `Address`, `Contact` and their vocabularies. Every domain module depends on it. |
| `person/` | The Person core plus its two conformance profiles (subject of care, connected person). |
| `placements/` | Children's Social Care Placements, plus `csv-metadata.json` (CSVW) describing the tabular CSV form. |
| `safeguarding/` | Safeguarding — organisations, services, professionals, service episodes, life events. |
| `assessments-and-plans/` | Care needs assessments and care plans. |
| `referrals/` | Referrals, requests and quality-of-care concerns. |
| `examples/` | Valid and invalid example records for every module and profile (see [Examples](#examples)). |
| `social-care.ttl` | The umbrella ontology that imports every module. |
| `social-care-shape.ttl` | All module shapes merged into one graph. |
| `context.jsonld` | The default JSON-LD context, composing the module contexts. |

## Which file should I use?

**To understand the vocabulary** — the classes, properties and controlled
vocabularies — use `social-care.ttl`. It declares no terms of its own; it
`owl:imports` each module, so load it with imports resolved to get the whole
standard as one graph.

**To validate data**, use the shape for the specific profile you are validating
against, not the umbrella:

| Validating | Shape |
| --- | --- |
| A person who is the subject of care | `person/person-subject-of-care-shape.ttl` |
| A connected or related person | `person/person-connected-shape.ttl` |
| A placement | `placements/placements-standard-shape.ttl` |
| A safeguarding record | `safeguarding/safeguarding-standard-shape.ttl` |
| An assessment or care plan | `assessments-and-plans/assessments-and-plans-standard-shape.ttl` |
| A referral, request or concern | `referrals/referrals-standard-shape.ttl` |

`social-care-shape.ttl` merges all of the above and takes the **subject-of-care**
cardinalities for `Person`. Use the profile shape directly if you are validating
connected people, or `Person` will be over-constrained.

There is deliberately no `person/person-standard-shape.ttl`: the core `Person`
is permissive by design so the profiles can tighten it, and a shape generated
from it would accept a person with no identifier, date of birth or address.

The shapes are generated only; there are no hand-maintained shapes. LinkML
`rules:` and class-level boolean expressions produce no SHACL, so any such
constraint in a schema is not enforced by these shapes.

## Examples

`examples/` holds example records organised as
`examples/<module>[/<profile>]/`:

```
examples/
├── assessments-and-plans/
├── person/
│   ├── connected/
│   └── subject-of-care/
├── placements/
├── referrals/
└── safeguarding/
```

- `valid-*.jsonld` / `valid-*.csv` conform to the module's shape (or, for CSV,
  to `placements/csv-metadata.json`).
- `invalid-*.jsonld` / `invalid-*.csv` each break the shape in a specific way.
- `expectations.json` lists, per invalid file, the violations it is expected to
  produce — the focus node, path and SHACL constraint for JSON-LD, or the row,
  column and error code for CSV.

The examples are checked against these shapes in
[SocialCareData/standard](https://github.com/SocialCareData/standard) before
they are synced here.

## Versioning

Each module is versioned on its own cadence. The module versions that make up
a MAIS release are pinned in `manifest.yaml` in
[SocialCareData/standard](https://github.com/SocialCareData/standard); that
file is not published here. Instead, `social-care.ttl` records the composed set
with `pav:version` on each module:

```turtle
sc:common     pav:version "1.0.0" .
sc:person     pav:version "1.0.0" .
sc:placements pav:version "2.0.0" .
...
```

## JSON-LD contexts

Each module ships the `context.jsonld` that maps JSON-LD data into these IRIs.
The root `context.jsonld` composes the module contexts by relative path, so keep
the directory layout intact if you vendor these files — or use the context from
a GitHub release, where those paths are rewritten to absolute URLs (see below).

## Releases

Publishing a GitHub release runs
[`release-artifacts.yml`](.github/workflows/release-artifacts.yml), which
attaches the artifacts to the release as flat files:

| Release asset | Source |
| --- | --- |
| `<name>.ttl`, `<name>-shape.ttl` | Every ontology and shape, unchanged. |
| `social-care.ttl` | The umbrella ontology, with its `owl:imports` pinned to the release tag instead of `main`. |
| `<module>-context.jsonld` | Each module's `context.jsonld`, renamed. |
| `context.jsonld` | The root context, with its module references rewritten to the versioned release URLs. |
| `<module>-csv-metadata.json` | Each module's CSVW `csv-metadata.json` (where it has one), renamed. |

The `examples/` directory is not attached to releases.

## How this repository is updated

A GitHub Action in `SocialCareData/standard` regenerates everything whenever the
LinkML schemas or examples change and opens a pull request here. Generation is
deterministic, so a pull request appears only when an artifact genuinely
changed.

See [`model-management.md`](model-management.md) for how the schemas are authored
and what the generators do and do not produce.

## Licence

These artifacts are published under the
[Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/),
as declared by the `license:` field of every source schema.
