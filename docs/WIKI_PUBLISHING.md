# ACP Wiki publishing and editorial rules

Source articles in `docs/wiki/*.md` must be reviewed in the code repository before being copied to the distinct GitHub Wiki Git repository. After an approved merge and initial wiki Home page setup, use `bash scripts/publish-github-wiki.sh --dry-run`; examine the diff, then run `bash scripts/publish-github-wiki.sh` with your standard Git credentials. The script preserves unrelated wiki pages and never syncs automatically.

Editorial rules follow ArchWiki-inspired principles: explain scope/prerequisites, prefer reproducible copyable commands, call out side effects, link specific source contracts/tests, write clear troubleshooting symptoms, avoid unsupported praise or speculation, and mark source-only, deployed, planned, deprecated and live-tested claims separately.

**Agent retrieval:** index source commit, audience, page slug, capability status and supporting file paths. Do not treat documentation as execution approval, leak tokens to prompts, infer live migration state from README text, or report an acceptance gate as passed without observed evidence. Retain links to the last known good run and regression test.