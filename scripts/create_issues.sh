#!/usr/bin/env bash
# Creates one GitHub issue per requirement in docs/backlog.tsv (the project backlog).
# Run ONCE, by one person (Aaruni), after:  gh auth login
#
#   DRY_RUN=1 bash scripts/create_issues.sh      # just prints what it would do
#   bash scripts/create_issues.sh                # really creates the issues
#
# Fill in the three GitHub usernames below before running for real.
set -euo pipefail

REPO="missyrue/Team4-SE-Project"
AARUNI_GH="missyrue"
AANYA_GH="Aanya-4"
ADITYA_GH="adityabadde"

handle() {            # team-member name -> GitHub username
  case "$1" in
    Aanya)  echo "$AANYA_GH" ;;
    Aaruni) echo "$AARUNI_GH" ;;
    Aditya) echo "$ADITYA_GH" ;;
  esac
}

# labels (ignore "already exists" errors)
mk_label() { [ "${DRY_RUN:-0}" = 1 ] && echo "label: $1" || gh label create "$1" --color "$2" --repo "$REPO" 2>/dev/null || true; }
mk_label "sprint-1" "0e8a16"; mk_label "sprint-2" "1d76db"
mk_label "functional" "5319e7"; mk_label "non-functional" "fbca04"; mk_label "security" "d93f0b"
for sp in 2 3 5; do mk_label "SP-$sp" "c5def5"; done

tail -n +2 docs/backlog.tsv | while IFS=$'\t' read -r key title type sprint owner sp module tests; do
  label_type=$(echo "$type" | tr 'A-Z' 'a-z')
  body="**Requirement:** $key ($type)
**Module:** $module
**Story points:** $sp
**Sprint:** $sprint
**Planned test case(s):** $tests

Source: SRS v1.0 section 4/5. Design: SAD v1.0. Tests: STP v1.0.

**Definition of done**
- [ ] Implemented and merged through a pull request (assignee raises the PR, repo owner reviews)
- [ ] Unit + integration tests written (normal + boundary/error cases)
- [ ] CI is green
- [ ] RTM status updated in docs/TRACEABILITY.md"
  cmd=(gh issue create --repo "$REPO" --title "$key: $title" --body "$body"
       --label "sprint-$sprint" --label "$label_type" --label "SP-$sp" --assignee "$(handle "$owner")")
  if [ "${DRY_RUN:-0}" = 1 ]; then echo "${cmd[@]}" | cut -c1-200; else "${cmd[@]}"; sleep 1; fi
done
