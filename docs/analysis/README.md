# Analysis & Implementation Reports (docs/analysis/README.md)

---

# 1. Purpose

This directory stores:

* Ticket-related **analysis documents**
* Post-implementation **reports**

This folder is the **single location for all ticket execution outputs**.

---

# 2. What Goes Here

---

## 2.1 Implementation Reports (Required)

Every completed ticket MUST generate a report here.

Reports include:

* What was implemented
* Which files were changed
* How verification was performed
* Whether the ticket is considered done

---

## 2.2 Analysis Documents (Optional)

Used for:

* Root cause analysis
* Technical investigation
* Pre-implementation design notes

---

## 2.3 Important Distinction

```txt
Analysis = before implementation (optional)
Report   = after implementation (required)
```

---

# 3. File Naming Rules (Strict)

---

## 3.1 Standard Format

```txt
{TICKET-ID}_report.md
```

---

## 3.2 Optional Extended Format

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

* Missing ticket ID
* Random naming
* Mixed inconsistent formats
* Using only "report.md" or generic names

---

# 4. Ticket ↔ Report Mapping

---

## 4.1 One-to-One Rule

```txt
1 Ticket = 1 Report
```

---

## 4.2 Expected Structure

```txt
docs/
  tickets/
    MS-01/
      BUG-004_...
  analysis/
    BUG-004_report.md
```

---

## 4.3 Linking (Recommended)

Tickets may optionally include:

```md
Report: docs/analysis/BUG-004_report.md
```

---

# 5. Report Content Requirements

Each report MUST follow the structure defined in:

```txt
docs/QA_AND_DONE.md
```

---

## Required Sections

* Summary
* Files Changed
* Implementation Details
* Verification
* Regression Check
* Risks / Notes
* Completion Status
* Final Status (updated after release verification)

---

# 6. Completion Status Rules

---

## 6.1 After Implementation

```txt
Implementation Done: YES
Release Verified: PENDING
```

---

## 6.2 After Deployment Verification

```txt
Release Verified: YES
Ticket Done: YES
```

---

## Important

> A report is NOT complete until Final Status is updated.

---

# 7. Workflow Integration

---

## Step 1. Ticket Implementation

* Cursor reads ticket from `docs/tickets/`
* Implements feature

---

## Step 2. QA Execution

* Run Verification steps from ticket
* Follow QA checklist in QA_AND_DONE.md

---

## Step 3. Report Creation

* Save report in `docs/analysis/`
* Follow naming rules
* Follow structure rules

---

## Step 4. Human Verification

* Deploy via CI/CD
* Verify on Oracle VM
* Confirm actual behavior

---

## Step 5. Final Update

* Update report Final Status
* Mark ticket as DONE

---

# 8. Important Rules

---

## 8.1 No Report = Not Done

If no report exists:

```txt
Ticket is NOT DONE
```

---

## 8.2 Wrong Location = Not Done

Reports must be in:

```txt
docs/analysis/
```

---

## 8.3 Naming Rule Violation = Invalid

If naming rule is not followed:

* Report is considered invalid
* Must be renamed

---

## 8.4 Always Follow QA_AND_DONE.md

This file defines:

* Definition of Done
* QA rules
* Report structure

---

# 9. Design Philosophy

---

## 9.1 Single Source of Truth

* QA_AND_DONE.md → defines rules
* analysis/ → stores outputs

---

## 9.2 Traceability

Every ticket must be traceable to:

```txt
Ticket → Implementation → Report → Verification → Done
```

---

## 9.3 Minimal but Strict

* Keep structure simple
* Enforce rules strictly

---

# 10. Final Summary

---

This directory ensures:

```txt
All implementations are:
- Documented
- Verified
- Traceable
- Reviewable
```

---

Without a report in this folder:

```txt
The work does not exist.
```
