# Safeguarding data model

The [Safeguarding Standard](../../../_pages/PUB02-safeguarding-standard.md) is
expressed as a single [LinkML](https://linkml.io/) schema. The SHACL, OWL/RDF,
JSON Schema and docs are generated from the YAML.

> For the LinkML → SHACL workflow — regenerating artifacts, how enums/codes map,
> conditional constraints, and validating the examples — see
> [`../model-management.md`](../model-management.md). **Don't edit the generated
> `*-shape.ttl` / `*.ttl` files directly.**

## Files

| File | Role |
| --- | --- |
| `safeguarding-standard.yaml` | **Authoritative source.** Prefixes, the five top-level classes (`Organisation`, `Service`, `Professional`, `ServiceEpisode`, `LifeEvent`), the linking/supporting objects (`SubjectPerson`, `RelatedProfessional`, `TimeInformation`, `Finding`, `Observation`, `Measurement`), every slot, and the controlled vocabularies (enums). The shared objects are **imported** from the common module (see below). |
| `../imports.json` | Top-level importmap shared by all modules: maps each module id (e.g. `https://ontology.socialcaredata.io/common`) to its local `*.yaml` file, so imports can be written as clean IRIs. |
| `safeguarding-standard-shape.ttl` | *Generated* SHACL — one `NodeShape` per class, including the imported `p:Identifier` / `p:Name` / `p:Address` / `p:Contact` shapes. |
| `safeguarding-standard.ttl` | *Generated* OWL/RDF ontology. Declares `owl:imports` of the common module and references the shared-object IRIs (`Identifier` …) rather than redefining them. |
| `context.jsonld` | JSON-LD context used by the examples. Maps friendly keys to the flat ontology predicates (including the shared objects' fields), and each coded value to its concept IRI. |
| `examples/` | JSON-LD examples. `valid-*.jsonld` must conform; `invalid-*.jsonld` must not. |

## Model shape

There is no single `tree_root`: the standard has **five** top-level entities,
each generated into its own `sh:targetClass` `NodeShape`, so a JSON-LD document
typed as any of them is validated against the matching shape.

Several friendly keys are **polymorphic** across classes and are disambiguated
by JSON-LD scoped contexts:

- `name` is a plain string on `Organisation`/`Service` but a `Name` object on
  `Professional` (all on predicate `sg:name`).
- `type` maps to a different coded predicate per class (`sg:organisationType`,
  `sg:serviceType`, `sg:episodeType`, `sg:eventType`) and, on `Observation` /
  `Measurement`, to `sg:observationType` / `sg:measurementType`.
- `contact` is multi-valued on `Organisation`/`Service` and exactly one on
  `Professional`.
- `relatedProfessional` is an `Identifier` reference on `Organisation`/`Service`
  but a qualified `RelatedProfessional` object on `ServiceEpisode`/`LifeEvent`.

### Shared objects

`Identifier`, `Name`, `Address` and `Contact` (and the `NameUseCode` /
`AddressUseCode` vocabularies) are **not** defined here — they are defined once
by the [Person Standard](../person/README.md) and imported from
`person-standard.yaml`. The safeguarding classes reference them by their Person
ontology IRIs (`p:Identifier`, `p:Name`, `p:Address`, `p:Contact`), and the
generated ontology carries `owl:imports p:schema`.

The import is written as the Person schema's canonical id rather than a relative
path, so the generated `owl:imports` is a clean IRI. `gen-shacl` / `gen-owl` are
told where that id lives on disk via `-im imports.json`; the `{% schema_table %}`
tool reads the same `imports.json`.

### Open (externally-governed) fields

Some fields deliberately are **not** modelled as closed enumerations, matching
the standard's prose:

- `involvement` (on `SubjectPerson` / `RelatedProfessional`) takes an HL7 v3
  `ParticipationType` code directly — modelled as an open string.
- `frequency` (on `TimeInformation`) is a FHIR `Timing`. This standard does not
  define or validate its structure — the value is an arbitrary JSON object
  (range `Any`) conforming to FHIR Timing.
- `Observation.type` draws from the extensible Observation Type Vocabulary
  (which has dynamic sub-parts such as `EAL.<ISO 639-1>`), so it is an open
  string rather than an enum.

## Regenerating

Run from this directory (see [`../model-management.md`](../model-management.md)):

```bash
gen-shacl --non-closed --suffix Shape -im imports.json safeguarding-standard.yaml > safeguarding-standard-shape.ttl
gen-owl --no-mergeimports -im imports.json --consolidate-cardinality-axioms --skip-vacuous-min-zero-cardinality-axioms --skip-vacuous-local-range-axioms safeguarding-standard.yaml > safeguarding-standard.ttl
```

`-im imports.json` resolves the Person import to the local file. `gen-shacl`
keeps `--include-imports` (the default) so the shared-object shapes are emitted
and validate the nested objects; `gen-owl` uses `--no-mergeimports` so the
Person classes are referenced via `owl:imports` rather than copied in.

## Validating the examples

```bash
cd ../../shacl/validation
npm install
node validate.js safeguarding
```
