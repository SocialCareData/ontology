# Placements data model

`placements-standard.yaml` is the [LinkML](https://linkml.io/) schema for the
Children's Social Care Placements data model (the `…-01.yaml` file is the current
working version). The SHACL, OWL/RDF, JSON Schema and docs are generated from it.

> For the LinkML → SHACL workflow — regenerating artifacts, how enums/codes map,
> conditional (`rules:`) constraints, and validating the examples — see
> [`../model-management.md`](../model-management.md). **Don't edit the generated
> `*-shape.ttl` / `*.ttl` files directly.**

## What's in the model

| Element | Count | Notes |
| --- | --- | --- |
| Classes | 7 | `Placement` (root) → `PlacementAvailability`, `PlacementRequirements`, `PlacementRecommendation`, `RiskAssessment`, `ActualPlacement`, `QualityAssurance` |
| Slots | 55 | datatypes, object references, controlled-vocabulary fields |
| Enums | 11 | one per SKOS concept scheme; each permissible value's `meaning:` is the concept IRI |
| Types | 1 custom | `nonNegativeInteger` → `xsd:nonNegativeInteger` |

`Placement` is the root record; the other classes hang off it as object
references (class-ranged slots). Controlled-vocabulary fields are enum-ranged
slots.

## Model-specific notes

- **Conditional "Other ⇒ free-text" rules.** Four fields require a paired
  free-text value when their `Other` concept is selected (`outOfLAReason`,
  `specificCommunicationRequirement`, `culturalNeeds`, `additionalSupport`).
  These are `rules:` in the schema and are enforced in SHACL via the
  hand-maintained `placements-base-rules-shape.ttl` (see
  [`../model-management.md`](../model-management.md#what-gen-shacl-does-not-generate)).
- **`totalWeeklyCost`** is bounded to £100–£100,000 (`minimum_value` /
  `maximum_value`).
