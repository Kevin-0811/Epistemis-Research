# Data and licensing policy

## Why the paper corpus is omitted

The earlier development repository contained research-paper PDFs, GROBID-extracted TEI XML, and intermediate JSONL datasets. The audit did not establish redistribution permission or explicit licensing for those materials. Extracted full text and derived training examples can still carry rights or contractual restrictions; conversion to TEI or JSONL does not automatically make them freely redistributable.

This cleaned branch therefore excludes:
- downloaded source-paper PDFs;
- full-text TEI extractions and temporary conversion output;
- intermediate, generated, training, and validation JSONL datasets;
- local debug and compiled Python files.

Keep these materials in a private, access-controlled archive unless each item's rights and provenance are checked.

## Use of external documents

Users must ensure they have the right to download, process, store, and share the documents they supply. Follow source, publisher, repository, and institutional terms. Do not commit papers, extracted full text, or derived datasets merely because they were technically accessible.

## Software licence

No open-source software licence has been selected. Until a licence is added by the author, all rights are reserved by default. Public visibility alone does not grant permission to reuse, modify, or redistribute the code.

## Provenance records

Before adding a corpus, keep a manifest with the source URL or DOI, author/title, retrieval date, applicable licence or permission, redistribution status, transformations applied, and required attribution. Do not store personal or access-controlled credentials in the manifest.
