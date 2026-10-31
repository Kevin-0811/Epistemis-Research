# Historical material

This directory preserves source snapshots and research notes from earlier iterations. It is not part of the installed runtime package.

Archived classifier and preprocessor versions have different interfaces and import assumptions. They may depend on local files, versions, or datasets that are intentionally not distributed here. They are not expected to run unchanged.

The DistilBERT/SciBERT protocols and planned architecture are historical design notes. They are not evidence that those models were implemented, trained, or evaluated in the current release.

The old JSONL-pushing utility was excluded because it ran preprocessing at import time and assumed a local text file and a legacy module path. The paper corpus and intermediate datasets were excluded because redistribution rights were not established.
