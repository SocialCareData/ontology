# Social Care MAIS ontology

OWL/RDF ontologies and SHACL shapes for the Social Care MAIS (Multi-Agency
Information Sharing) data standards, published under the single flat namespace
`https://ontology.socialcaredata.io/`.

> ## Everything here is generated — do not edit
>
> These files are produced from the LinkML schemas in
> [SocialCareData/standard](https://github.com/SocialCareData/standard) under
> `src/_data/model/`, and are overwritten on every sync. Edit the LinkML YAML
> there and let the sync republish; changes made directly in this repository
> will be silently reverted.

## Layout

One directory per module, mirroring the source tree. Each LinkML schema yields
an ontology (`<name>.ttl`) and, where applicable, a SHACL shape
(`<name>-shape.ttl`).

| Directory | Contents |
| --- | --- |
| `common/` | Shared building blocks — `Identifier`, `Name`, `Address`, `Contact` and their vocabularies. Every domain module depends on it. |
| `person/` | The Person core plus its two conformance profiles. |
| `placements/` | Children's Social Care Placements, current and frozen earlier versions. |
| `safeguarding/` | Safeguarding — organisations, services, professionals, service episodes, life events. |
| `assessments-and-plans/` | Care needs assessments and care plans. |
| `mais/` | The merged umbrella ontology and the release manifest. |

## Which file should I use?

**To understand the vocabulary** — the classes, properties and controlled
vocabularies — use `mais/mais.ttl`. It is the whole standard merged into one
graph, with every module's terms resolved into the flat namespace.

**To validate data**, use the shape for the specific profile you are validating
against, not the umbrella:

| Validating | Shape |
| --- | --- |
| A person who is the subject of care | `person/person-subject-of-care-shape.ttl` |
| A connected or related person | `person/person-connected-shape.ttl` |
| A placement | `placements/placements-standard-shape.ttl` |
| A safeguarding record | `safeguarding/safeguarding-standard-shape.ttl` |
| An assessment or care plan | `assessments-and-plans/assessments-and-plans-standard-shape.ttl` |

`mais/mais-shape.ttl` merges all of the above and takes the **subject-of-care**
cardinalities for `Person`. Use the profile shape directly if you are validating
connected people, or `Person` will be over-constrained.

There is deliberately no `person/person-standard-shape.ttl`: the core `Person`
is permissive by design so the profiles can tighten it, and a shape generated
from it would accept a person with no identifier, date of birth or address.

Some constraints cannot be expressed in generated SHACL — LinkML `rules:` and
boolean expressions produce no shapes. Those are hand-maintained in the source
repository (for example placements' "Other ⇒ free-text required" rules) and are
**not** published here. Generated shapes alone are necessary but not sufficient.

## Versioning

`mais/manifest.yml` pins the module versions that compose a MAIS release:

```yaml
mais_version: 2026.1.0
modules:
  common: 1.0.0
  person: 1.0.0
  placements: 2.0.0
  ...
```

Each module is versioned on its own cadence; a release records a compatible set
and `mais/mais.ttl` is generated from it.

Where a module keeps frozen earlier versions, the current one holds the bare
ontology IRI and the frozen ones are version-qualified, so no two files claim
the same identity:

| File | Ontology IRI |
| --- | --- |
| `placements/placements-standard.ttl` | `https://ontology.socialcaredata.io/placements` |
| `placements/placements-standard-v1.ttl` | `https://ontology.socialcaredata.io/placements/1.0.0` |
| `placements/placements-standard-v0_1.ttl` | `https://ontology.socialcaredata.io/placements/0.1.0` |

## JSON-LD contexts

Each module ships the `context.jsonld` that maps JSON-LD data into these IRIs.
`mais/context.jsonld` composes the module contexts by relative path, so keep the
directory layout intact if you vendor these files.

## How this repository is updated

A GitHub Action in `SocialCareData/standard` regenerates everything whenever the
LinkML schemas change, validates the standards' examples against the fresh
shapes, and opens a pull request here. Generation is deterministic, so a pull
request appears only when an artifact genuinely changed.

See [`model-management.md`](model-management.md) for how the schemas are authored
and what the generators do and do not produce.

## Licence

These artifacts are published under the
[Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/),
as declared by the `license:` field of every source schema.
