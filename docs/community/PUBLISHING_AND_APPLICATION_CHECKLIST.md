# Publishing and Claude for OSS Checklist

This checklist keeps the public launch and Claude for OSS application evidence
auditable. Do not use fake accounts, sockpuppet PRs, or meaningless PR splits.
The target is real community contribution, not a cosmetic metric.

## 1. Publish the clean repository

Create an empty public GitHub repository, either manually or with the helper:

```bash
cd /Users/ijeong-geun/OSS/ai-language-partner
GITHUB_TOKEN=... python scripts/create_github_repository.py sinmb79/ai-language-partner
```

Or run the full bootstrap after `GITHUB_TOKEN` is available:

```bash
cd /Users/ijeong-geun/OSS/ai-language-partner
GITHUB_TOKEN=... scripts/bootstrap_public_github_repo.sh sinmb79/ai-language-partner
```

Manual settings:

- Owner: `sinmb79`
- Name: `ai-language-partner`
- Visibility: public
- Do not initialize with README, license, or `.gitignore`

Then push the prepared source-only snapshot:

```bash
cd /Users/ijeong-geun/OSS/ai-language-partner
git remote add origin git@github.com:sinmb79/ai-language-partner.git
git push -u origin main
```

If SSH is not configured, use:

```bash
git remote add origin https://github.com/sinmb79/ai-language-partner.git
git push -u origin main
```

## 2. Bootstrap community metadata

Use a GitHub token with repo issue/label permissions:

```bash
cd /Users/ijeong-geun/OSS/ai-language-partner
GITHUB_TOKEN=... python scripts/create_github_labels.py sinmb79/ai-language-partner
GITHUB_TOKEN=... python scripts/create_github_issue_seeds.py sinmb79/ai-language-partner
```

Open the repository settings and enable:

- Issues
- Discussions, if available
- Actions
- Dependency graph and Dependabot alerts
- Branch protection for `main` after the initial push

## 3. Verify the public snapshot

Run these before sharing the repo:

```bash
cd /Users/ijeong-geun/OSS/ai-language-partner
python3 scripts/check_public_tree.py

cd apps/api
.venv/bin/python -m pytest

cd ../mobile
npm run verify
```

Expected current baseline:

- Public tree scan passes
- Backend pytest passes in mock mode
- Mobile TypeScript/regression verification passes
- `npm audit` still reports Expo SDK 52 transitive advisories; track this as a
  real public issue rather than force-upgrading blindly

## 4. Phase A application

Apply only as a long-shot exception before the numeric threshold is met. Use
the text in `docs/CLAUDE_FOR_OSS_APPLICATION.md` and be explicit that the repo
does not yet meet the official numeric tracks.

Evidence to include:

- Repo URL
- Green Actions URL
- Public docs and contribution system
- Local-first/no-runtime-LLM architecture rationale

## 5. Phase B application

This is the main approval route. Apply after the repo has at least 20 unique
external contributors with merged PRs in the last 12 months.

Run:

```bash
cd /Users/ijeong-geun/OSS/ai-language-partner
GITHUB_TOKEN=... python scripts/export_claude_for_oss_evidence.py sinmb79/ai-language-partner --since 2025-07-08
GITHUB_TOKEN=... python scripts/verify_claude_for_oss_readiness.py sinmb79/ai-language-partner
```

Copy the generated Markdown table into
`docs/CLAUDE_FOR_OSS_APPLICATION.md`.

Counting rules:

- Count one meaningful merged PR per external contributor
- Exclude `sinmb79`, bots, duplicate identities, and maintainer-authored PRs
- Keep issue links and review comments on every counted PR
- Docs-only PRs count only when they improve real user/contributor experience

## 6. Application sentence

Use a plain claim:

> I maintain `ai-language-partner`, a local-first open-source Japanese learning
> app for Korean speakers. The project has 20+ unique external contributors
> with merged PRs in the last 12 months. Its architecture avoids runtime
> LLM/API dependency for the core speaking loop, making it useful for low-cost
> education deployments where latency, privacy, and per-turn API cost matter.
