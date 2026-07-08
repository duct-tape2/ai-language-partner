## Summary

-

## Type

- [ ] Bug fix
- [ ] Feature
- [ ] Documentation
- [ ] Language/content review
- [ ] Test or tooling

## Checklist

- [ ] I linked the issue this PR closes or advances.
- [ ] I kept the change focused enough for review.
- [ ] I did not add generated clips, archives, local engine files, databases, or secrets.
- [ ] I preserved the no-runtime-LLM rule for Daily Talk.
- [ ] I ran the relevant checks:
  - [ ] `cd apps/api && python -m pytest`
  - [ ] `cd apps/mobile && npm run verify`

## Notes for Reviewers

-

Maintainers: leave a human review comment before merging any PR that might be
counted for Claude for OSS evidence. The automated welcome comment is not a
review decision, and neither is the automated review-packet comment. Use
`python scripts/build_pr_review_packet.py duct-tape2/ai-language-partner <PR_NUMBER>`
or `docs/community/MAINTAINER_PR_REVIEW_RUNBOOK.md` for the review sequence.
