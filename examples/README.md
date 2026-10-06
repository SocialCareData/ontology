# Examples

Worked JSON-LD records for every standard. Unlike the rest of this repository
they are written by hand, not generated, and the sync from
[SocialCareData/standard](https://github.com/SocialCareData/standard) leaves
this folder alone.

They serve three purposes: they show what a conforming record looks like, they
are the "load an example" fixtures in the
[validator](https://socialcaredata.github.io/validator/), and they are the
validator's conformance suite. The page fetches them from `main`, by the URLs
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

The validator also pins the issue codes and JSON paths every invalid example
should produce, in its `test/expectations/`. A new or changed invalid example
needs those regenerated there. To check a change here against the validator:

```bash
cd ../validator
ONTOLOGY_DIR=../ontology npm test
```

Each file declares the ontology's released combined context,
`https://github.com/SocialCareData/ontology/releases/latest/download/context.jsonld`,
so it resolves for any JSON-LD processor. The validator does not use it: it
substitutes the standard's module context, the one matching the shapes, and
reports `substituted-context`. See the validator's `src/config.ts` for why.
