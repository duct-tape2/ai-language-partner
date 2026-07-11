## Summary

-

## Linked Issue

Closes #ISSUE_NUMBER

## Type

- [ ] Bug fix
- [ ] Feature
- [ ] Documentation
- [ ] Language/content review
- [ ] Test or tooling

## Checklist

- [ ] I linked the issue this PR closes or advances with `Closes #...` or `Refs #...`.
- [ ] I kept the change focused enough for review.
- [ ] I did not add generated clips, archives, local engine files, databases, or secrets.
- [ ] I preserved the no-runtime-LLM rule for Daily Talk.
- [ ] I ran the relevant checks:
  - [ ] Docs/content review only; no local setup required.
  - [ ] `python3 scripts/check_public_tree.py`
  - [ ] `cd apps/api && .venv/bin/python -m pytest`
  - [ ] `cd apps/mobile && npm run verify`
  - [ ] `python3 -m unittest discover -s scripts -p 'test_*.py'`

## Notes for Reviewers

-

## New Contributor Route

- Five-minute first PR: https://duct-tape2.github.io/ai-language-partner/community/FIVE_MINUTE_FIRST_PR.html
- Directory first PR fast lane: https://duct-tape2.github.io/ai-language-partner/community/DIRECTORY_FIRST_PR.html
- Codespaces first PR: https://duct-tape2.github.io/ai-language-partner/community/CODESPACES_FIRST_PR.html
- First PR help desk: https://github.com/duct-tape2/ai-language-partner/discussions/53

Maintainers: leave a human review comment before merging. The automated welcome
comment is not a review decision, and neither is the automated review-packet
comment. Use
`python scripts/build_pr_review_packet.py duct-tape2/ai-language-partner <PR_NUMBER>`
or `docs/community/MAINTAINER_PR_REVIEW_RUNBOOK.md` for the review sequence.
