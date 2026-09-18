# Care Needs Assessments and Care Plans data model

The [Assessments and Plans Standard](../../../_pages/PUB05-assessments-and-plans-standard.md)
is expressed as a single [LinkML](https://linkml.io/) schema. The SHACL, OWL/RDF,
JSON Schema and docs are generated from the YAML.

> For the LinkML → SHACL workflow — regenerating artifacts, how enums/codes map,
> conditional constraints, and validating the examples — see
> [`../model-management.md`](../model-management.md). **Don't edit the generated
> `*-shape.ttl` / `*.ttl` files directly.**

## Files

| File | Role |
| --- | --- |
| `assessments-and-plans-standard.yaml` | **Authoritative source.** Prefixes, the two top-level classes (`CareNeedsAssessment`, `CarePlan`), the `FoundationalInformation` mixin they share, the supporting objects (`Review`, `AssessmentQuestion`, `CareComponent`, `CareActor`, `CareTiming`, `CareActivity`), every slot, and the controlled vocabularies (enums). `Identifier` is **imported** from the common module (see below). |
| `../imports.json` | Top-level importmap shared by all modules: maps each module id (e.g. `https://ontology.socialcaredata.io/common`) to its local `*.yaml` file, so imports can be written as clean IRIs. |
| `assessments-and-plans-standard-shape.ttl` | *Generated* SHACL — one `NodeShape` per class, including the imported `p:Identifier` shape. |
| `assessments-and-plans-standard.ttl` | *Generated* OWL/RDF ontology. Declares `owl:imports` of the common module and references `Identifier` rather than redefining it. |
| `context.jsonld` | JSON-LD context used by the examples. Maps friendly keys to the flat ontology predicates (including the shared object's fields), and each coded value to its concept IRI. |
| `examples/` | JSON-LD examples. `valid-*.jsonld` must conform; `invalid-*.jsonld` must not. |

## Model shape

There is no single `tree_root`: the standard has **two** top-level entities —
`CareNeedsAssessment` and `CarePlan` — each generated into its own
`sh:targetClass` `NodeShape`, so a JSON-LD document typed as either one is
validated against the matching shape.

Both entities carry the same block of foundational information (`identifier`,
`personId`, `professionalId`, `dateCompleted`, `capacityToCompleteAssessment`,
`advocateRequired`, `consentToInformationSharing`, `review`,
`serviceEpisodeId`), modelled as the `FoundationalInformation` **mixin**. Each
entity then declares only its own slots; the inherited ones are not repeated.
`gen-shacl`, `gen-owl` and the `{% schema_table %}` documentation tool all
resolve the mixin, and the tables list the inherited slots first (in mixin
declaration order) followed by the class's own slots.

> **Don't narrow an inherited slot with `slot_usage` here.** For a slot a class
> inherits from a mixin but does not declare itself, `gen-owl` re-derives an
> induced slot that loses its `range` and falls back to the schema's
> `default_range`, emitting an `owl:allValuesFrom xsd:string` axiom that
> contradicts the slot's real range (so `dateCompleted` ends up locally a string
> and globally an `xsd:dateTime`). The shared slots are therefore worded to cover
> both cases ("this assessment / plan"). If a genuine per-entity difference is
> needed, either add the slot to that entity's own `slots:` as well, or repeat
> `range:` inside the `slot_usage` block, and check the generated ontology for
> stray `allValuesFrom` axioms (there should be none).

`serviceEpisodeId` references a [Safeguarding
`ServiceEpisode`](../safeguarding/README.md) by `Identifier`; the Safeguarding
schema is not imported, so there is no cross-schema dependency in either
direction.

### Shared objects

`Identifier` is **not** defined here — it is defined once by the
[Person Standard](../person/README.md) and imported from `person-standard.yaml`.
The assessment and plan classes reference it by its Person ontology IRI
(`p:Identifier`), and the generated ontology carries `owl:imports p:schema`.

Two consequences to keep in mind when editing the YAML:

- **Never define `value` or `system` slots here.** They belong to `p:Identifier`.
  A same-named slot in this schema overrides the imported one, which would rebind
  `p:Identifier`'s properties to `ap:` IRIs — an identifier written against this
  standard would then no longer match the same object in the Person and
  Safeguarding standards.
- For the same reason this schema's own identifier slot is named
  **`apIdentifier`** (with `title: identifier` and `slot_uri: ap:identifier`),
  so it does not override the Person Standard's `identifier` slot, which is
  `0..*` on `Person`. The documentation, the predicate and the JSON-LD key all
  still read `identifier`.

### Vocabularies that are not bound to a slot

`ClientFundingStatus` and `CareActEligibilityStatus` are the answer vocabularies
for the statutory questions `STAT-FINANCE-01` and `CA-ELIGIBILITY-01`. Because
`AssessmentQuestion.answer` is deliberately an open string (its parsing is
declared by `answerType`), these enums are published as reference vocabularies
and are **not** the range of any slot, so `gen-shacl` emits no `sh:in` for them.

`StatutoryQuestionId` is likewise a reference dictionary: `questionId` is an open
string, since local authorities may also use their own local IDs for
non-statutory questions.

## Regenerating

Run from this directory (see [`../model-management.md`](../model-management.md)):

```bash
gen-shacl --non-closed --suffix Shape -im imports.json assessments-and-plans-standard.yaml > assessments-and-plans-standard-shape.ttl
gen-owl --no-mergeimports -im imports.json --consolidate-cardinality-axioms --skip-vacuous-min-zero-cardinality-axioms --skip-vacuous-local-range-axioms assessments-and-plans-standard.yaml > assessments-and-plans-standard.ttl
```

`-im imports.json` resolves the Person import to the local file. `gen-shacl`
keeps `--include-imports` (the default) so the shared-object shapes are emitted
and validate the nested objects; `gen-owl` uses `--no-mergeimports` so the
Person classes are referenced via `owl:imports` rather than copied in.

## Validating the examples

```bash
cd ../../shacl/validation
npm install
node validate.js assessments-and-plans
```
