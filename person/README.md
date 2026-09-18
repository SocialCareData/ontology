# Person data model

The Person Standard is expressed as a [LinkML](https://linkml.io/) shared core
plus two conformance profiles. The SHACL, OWL/RDF, JSON Schema and docs are
generated from the YAML.

> For the LinkML → SHACL workflow — regenerating artifacts, how enums/codes map,
> conditional constraints, and validating the examples — see
> [`../model-management.md`](../model-management.md). **Don't edit the generated
> `*-shape.ttl` files directly.**

## The two-profile design

Whether a person is the **subject of care** or merely a **connected/related**
person changes the cardinality of several `Person` properties. This is expressed
as a shared core plus two profiles:

| File | Role |
| --- | --- |
| `person-standard.yaml` | **Shared core.** Prefixes, controlled vocabularies (enums), every slot definition (ranges, patterns, descriptions), the six sub-entity classes (`Identifier`, `Name`, `Address`, `Contact`, `PersonRelationship`, `PartialDate`), and a canonical base `Person`. |
| `person-subject-of-care.yaml` | Imports the core and redefines `Person`, **tightening** cardinalities (identifier, dateOfBirth, isDeceased, address, genderCode, ethnicityCode become required). |
| `person-connected.yaml` | Imports the core and redefines `Person` so all demographics are optional and `contact` / `relatedPerson` are limited to at most one. |

Each profile fully redefines `Person` (LinkML replaces, rather than merges, an
imported class), so generating SHACL from a profile emits exactly one
`p:PersonShape` plus the shared sub-entity shapes — no stray shapes. Because both
profiles inherit the identical sub-entity and vocabulary definitions from the
core, those shapes come out equivalent across the two files. Always generate from
a **profile** file (never the core), so `Person` carries a concrete cardinality.

### Person cardinalities

| Property | Subject of care | Connected |
| --- | --- | --- |
| `identifier` | 1..* | 0..* |
| `name` | 1..1 | 1..1 |
| `dateOfBirth` | 1..1 | 0..1 |
| `isDeceased` | 1..1 | 0..1 |
| `deceasedDate` | 0..1 | 0..1 |
| `address` | 1..* | 0..* |
| `contact` | 0..* | 0..1 |
| `genderCode` | 1..1 | 0..1 |
| `sexCode` | 0..1 | 0..1 |
| `ethnicityCode` | 1..1 | 0..1 |
| `relatedPerson` | 0..* | 0..1 |
| `primaryContactProfessional` | 0..* | 0..* |
| `matchedPersonRef` | 0..* | 0..* |

## Model-specific notes

The generated shapes are functionally equivalent to the hand-written
`manual-person-*-shacl-shape.ttl` files (same target classes, cardinalities,
`sh:in` lists and patterns). Two constraints in the manual shapes are **not**
reproduced, by design:

- **`sh:minLength 1`** on `value` / `familyName` / `givenName` / `line1` / `city`
  (LinkML has no min-length facet). No example relies on it — empty-value cases
  are already caught by `minCount`.
- The **`deceasedDate` warning** (subject-of-care: `isDeceased=true` with no
  `deceasedDate` → `sh:Warning`) — a conditional constraint `gen-shacl` cannot
  produce (see
  [`../model-management.md`](../model-management.md#what-gen-shacl-does-not-generate)).
  It is advisory only and no example triggers it.
