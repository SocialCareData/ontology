# Referrals and Requests Standard data model

The [Referrals and Requests Standard](../../../_pages/PUB06-referrals-standard.md)
is expressed as a single [LinkML](https://linkml.io/) schema. The SHACL, OWL/RDF,
JSON Schema and docs are generated from the YAML.

> For the LinkML → SHACL workflow — regenerating artifacts, how enums/codes map,
> conditional constraints, and validating the examples — see
> [`../model-management.md`](../model-management.md). **Don't edit the generated
> `*-shape.ttl` / `*.ttl` files directly.**

## Files

| File | Role |
| --- | --- |
| `referrals-standard.yaml` | **Authoritative source.** Prefixes, the three core classes (`Referral`, `Request`, `QualityOfCareConcern`), supporting tuple objects (`HouseholdMember`, `ReferrerDetails`, `ConcernDetail`, `ReferralInvolvement`, `DocumentReference`, `ReferralRelationship`, `ReferralAssessmentQuestion`), slots, and controlled vocabularies. Imports `common`, `person`, and `safeguarding`. |
| `../imports.json` | Top-level importmap shared by all modules: maps each module id (e.g. `https://ns.socialcaredata.io/referrals`) to its local `*.yaml` file. |
| `context.jsonld` | JSON-LD context used by examples and external consumers. |
