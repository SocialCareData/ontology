# Examples

Worked JSON-LD records for every standard. Unlike the rest of this repository
they are written by hand, not generated, and the sync from
[SocialCareData/standard](https://github.com/SocialCareData/standard) leaves
this folder alone.

They serve three purposes: they show what a conforming record looks like, they
are the "load an example" fixtures in the
[validator](https://socialcaredata.github.io/validator/), and they are the
shapes' conformance suite. The page fetches them from `main`, by the URLs
listed in the validator's `src/config.ts`, so a new or changed example reaches
it once merged here.

The naming convention is load-bearing:

- **`valid-*.jsonld`** must conform.
- **`invalid-*.jsonld`** must not.

Each folder has exactly two valid records, and they are the ones the validator
offers under "Load an example". Its `src/config.ts` lists them, and a test
there fails if the list and the folder disagree:

- **`valid-<name>.jsonld`** carries only what the standard requires - the
  smallest record that conforms.
- **`valid-<name>-full.jsonld`** gives every property the shape defines at least
  one value.

Where a standard covers several record types (safeguarding, assessments and
plans), both files hold one node per type in a top-level `@graph`.

A JSON key the context does not define is silently dropped by JSON-LD, so a
misspelt property in a "full" example still conforms while testing nothing.
Check a new property actually reaches the RDF.

Each file declares the ontology's released combined context,
`https://github.com/SocialCareData/ontology/releases/latest/download/context.jsonld`,
so it resolves for any JSON-LD processor. The validator does not use it: it
substitutes the standard's module context, the one matching the shapes, and
reports `substituted-context`. See the validator's `src/config.ts` for why.

## Checking them

`.github/scripts/validate_examples.py` validates every record with
[pySHACL](https://github.com/RDFLib/pySHACL), using this commit's shapes and
module context. The *Validate examples* workflow runs it on every pull request.

```bash
pip install pyshacl
python .github/scripts/validate_examples.py            # check
python .github/scripts/validate_examples.py --update   # regenerate expectations.json
```

Each folder's `expectations.json` pins the violations that each invalid record
must produce. For every violation it records the type of the failing node, the
property, and the SHACL constraint, all in the record's own terms:

```json
"invalid-bad-postcode.jsonld": [
  { "focus": "Address", "path": "postcode", "constraint": "sh:pattern" }
]
```

These pins mean an invalid example can't start failing for the wrong reason,
or for extra reasons, without the check failing. Any change counts: a
violation added, one gone, or one moved. The check also fails when an invalid
record has no entry. After adding or changing an invalid example, or when a
shape change moves what it reports, run `--update` and **read the diff**
before committing. Regenerating records whatever the shapes currently say,
including any mistake you have just made.
