# QA & Definition of Done (QA_AND_DONE.md)

---

# 1. Purpose

This document defines:

* Definition of Done (DoD)
* QA (Verification) 기준
* Ticket 완료 판정 기준
* Implementation Report 작성 규칙

This file acts as the **single source of truth (SSOT)** for:

* When a ticket is considered DONE
* How QA is performed
* Where and how reports are written

---

# 2. Definition of Done (DoD)

A ticket is considered **DONE** only when **ALL** conditions below are satisfied:

---

## 2.1 Functional Completion

* [ ] All Acceptance Criteria are satisfied
* [ ] Implementation matches the intended behavior described in the ticket
* [ ] No missing functionality within defined scope

---

## 2.2 Scope Compliance

* [ ] Only allowed files / logic were modified
* [ ] No unintended side effects introduced
* [ ] No unrelated refactoring performed

---

## 2.3 Report Completion

* [ ] Implementation report exists under `docs/analysis/`
* [ ] Report follows naming rules (see Section 4)
* [ ] Report includes required sections (see Section 5)

---

## 2.4 QA (Verification)

* [ ] All Verification steps defined in the ticket are executed
* [ ] All scenarios pass as expected
* [ ] Core user flow works correctly
* [ ] No regression observed in related features

---

## 2.5 Release Verification (Critical)

* [ ] Changes are deployed via CI/CD
* [ ] Verified on **Oracle VM running environment**
* [ ] Verified through actual browser interaction
* [ ] UI/UX behaves as expected in production-like environment

---

## 2.6 Final Human Validation

* [ ] Final verification performed by human
* [ ] Merge decision approved

---

## ✅ Final Rule

> A ticket is NOT DONE until **Release Verification (Oracle VM)** is confirmed.

---

# 3. QA (Verification) Guidelines

QA is divided into two levels:

---

## 3.1 Ticket-Level Verification (Required)

Defined in each ticket:

* Verification steps must be executed exactly
* All expected results must match

---

## 3.2 Minimal QA Checklist (Project-Level)

Every ticket must pass this checklist:

```txt
- Acceptance Criteria verified
- Core user flow works
- No regression observed
- Report exists and is readable
- Verified on deployed environment (Oracle VM)
```

---

# 4. Report Location & Naming Rules

---

## 4.1 Location

All implementation reports MUST be stored in:

```txt
docs/analysis/
```

---

## 4.2 File Naming Convention

Use ONE of the following formats:

```txt
{TICKET-ID}_report.md
```

or

```txt
{TICKET-ID}_{short-description}_report.md
```

---

## Examples

```txt
BUG-004_report.md
UX-001_persona_toast_message_report.md
```

---

## 🚫 Not Allowed

* Random file names
* Missing ticket ID
* Mixed naming patterns

---

# 5. Report Structure (Required)

Each report MUST include the following sections:

---

## 5.1 Summary

* What was implemented
* Why the change was needed

---

## 5.2 Files Changed

* List of modified files
* Brief description per file

---

## 5.3 Implementation Details

* Key logic changes
* Important decisions

---

## 5.4 Verification

* Steps executed
* Results per step

Example:

```md
### Case 1: Character Chat (new session)
- result: PASS

### Case 2: World Chat
- result: PASS
```

---

## 5.5 Regression Check

* Confirm no existing features are broken

---

## 5.6 Risks / Notes

* Any potential edge cases
* Known limitations (if any)

---

## 5.7 Completion Status (Required)

```md
## Completion Status

- Implementation Done: YES
- Release Verified: PENDING
```

---

## 5.8 Final Status (Human Updated)

After manual verification:

```md
## Final Status

- Release Verified: YES
- Ticket Done: YES
```

---

# 6. Ticket Completion Flow

---

## Step 1. Ticket Created

* Stored under `docs/tickets/`
* Includes Acceptance Criteria and Verification

---

## Step 2. Implementation

* Cursor implements based on ticket
* Scope strictly followed

---

## Step 3. QA Execution

* Run ticket Verification steps
* Run minimal QA checklist

---

## Step 4. Report Creation

* Save report in `docs/analysis/`
* Follow naming + structure rules

---

## Step 5. Implementation Done

* Mark:

```txt
Implementation Done: YES
Release Verified: PENDING
```

---

## Step 6. Release Verification (Human)

* Deploy via CI/CD
* Check Oracle VM environment
* Verify actual behavior

---

## Step 7. Final Done

* Update report:

```txt
Release Verified: YES
Ticket Done: YES
```

---

# 7. Roles & Responsibilities

---

## AI (Cursor)

Must:

* Implement according to ticket
* Execute Verification steps
* Create report following rules
* Mark Implementation Done

---

## Human (You)

Must:

* Verify on deployed environment (Oracle VM)
* Confirm real UI/UX behavior
* Decide final merge

---

# 8. Important Principles

---

## 8.1 Ticket-Driven Development

* Every change must come from a ticket
* No direct implementation without ticket

---

## 8.2 Small, Controlled Changes

* 1 ticket = 1 logical change
* Avoid large, risky modifications

---

## 8.3 Verification Over Assumption

* "Looks correct" is NOT enough
* Must verify via defined steps

---

## 8.4 Deployment is Part of Done

* Local success ≠ Done
* Production-like verification is mandatory

---

# 9. Final Summary

---

A ticket is DONE only when:

```txt
Code implemented
+ QA verified
+ Report written
+ Deployed
+ Verified on Oracle VM
+ Human approved
```

---

This document defines the **minimum standard for quality and completion** in this project.
