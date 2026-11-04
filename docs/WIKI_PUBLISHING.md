# ACP Wiki publishing and editorial rules

Source articles in `docs/wiki/*.md` must be reviewed in the code repository before being copied to the distinct GitHub Wiki Git repository. After an approved merge and initial wiki Home page setup, use `bash scripts/publish-github-wiki.sh --dry-run`; examine the diff, then run `bash scripts/publish-github-wiki.sh` with your standard Git credentials. The script preserves unrelated wiki pages and never syncs automatically.

Editorial rules follow ArchWiki-inspired principles: explain scope/prerequisites, prefer reproducible copyable commands, call out side effects, link specific source contracts/tests, write clear troubleshooting symptoms, avoid unsupported praise or speculation, and mark source-only, deployed, planned, deprecated and live-tested claims separately.

**Agent retrieval:** index source commit, audience, page slug, capability status and supporting file paths. Do not treat documentation as execution approval, leak tokens to prompts, infer live migration state from README text, or report an acceptance gate as passed without observed evidence. Retain links to the last known good run and regression test.

## Automatic publishing from `dev`

After review and merge of `.github/workflows/publish-github-wiki.yml` to `dev`, changing `docs/wiki/` on `dev` validates the versioned Guide index and publishes managed Markdown pages to this repository's separate native GitHub Wiki. The job uses the built-in short-lived GitHub Actions `GITHUB_TOKEN` with `contents: write` and `gh auth setup-git`, a dry-run, and GitHub's native Wiki Git remote. No vendor LLM API token or personal GitHub PAT is normally required.

**Initialize once:** in GitHub repository Settings → General → Features, enable Wikis; open Wiki → Create the first page → save a `Home` page. Otherwise the `.wiki.git` remote does not yet exist and the job fails. Run only after reviewed changes reach `dev`, and verify the workflow result plus actual Wiki Home/sidebar. This publishes **development documentation**, not independently verified production status.

You may also publish manually: authenticate with `gh auth login` / `gh auth setup-git`, check out `dev`, then run `bash scripts/publish-github-wiki.sh --dry-run` followed by `bash scripts/publish-github-wiki.sh`. `workflow_dispatch` is declared but GitHub's Actions UI may not expose manual runs until the workflow is also present on the default branch. Changes to unrelated native Wiki pages are preserved by this script; roll back via reviewed `dev` documentation or the native Wiki Git history. Repositories can restrict Actions token permissions, in which case review the job failure before changing credential strategy.

## Native Wiki HTML navigation

Repository Markdown links such as `[Getting started](Getting-started.md)` are correct for `docs/wiki/` file browsing, but the native GitHub Wiki may send readers to raw `.md` pages. The rendered page is `https://github.com/nyameko/agent-control-plane/wiki/Page-Slug` (no .md). Our publisher now calls `scripts/prepare_github_wiki.py`: it transforms local Wiki page links to canonical rendered Wiki URLs **only in the copied Wiki files**, while preserving original version-controlled Markdown links. Other relative files such as `guide-index.json` resolve to `blob/dev` Git sources. External links and fenced/inline code are not rewritten, and missing local links stop publication. PR CI runs offline regression tests and previews the rendered Wiki source; no Wiki writes happen until a reviewed merge into `dev`.
