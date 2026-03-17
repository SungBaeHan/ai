# UX-001 Persona Toast Message Unification

Unify persona confirmation toast message across Character / World / Game chat.

---

# Metadata

Type: TASK
Severity: minor
Layer: adapter
Milestone: MS-01

---

# Problem

Persona selection toast messages are inconsistent across chat types.

Current behavior:

* Character / World:

  * `페르조나가 선택되었습니다. 메시지를 보내면 적용됩니다`
* Game:

  * `페르조나가 적용되었습니다.`

Expected behavior:

* All chat types should display the same message:

  * `페르조나가 적용되었습니다.`

Impact:

* Inconsistent UX across similar actions
* Internal implementation differences (pending vs applied) are exposed to users
* Potential confusion and reduced product polish

---

# Context

Persona selection is handled in modal confirmation logic.

Relevant files:

* apps/web-html/chat.html
* apps/web-html/world.html
* apps/web-html/game.html

Key functions:

* confirmPersonaSelection()
* showToast()

Architecture hint:

UI Layer → Local State (PENDING or SESSION) → API (optional)

This ticket only affects UI messaging, not state logic.

---

# Scope

Allowed:

* Modify toast message strings
* Remove conditional message variations
* Ensure consistent message across all chat types

Not allowed:

* Changing persona application logic
* Modifying API behavior
* Refactoring state management (PENDING_PERSONA_ID)
* Any unrelated UI or feature changes

---

# Strategy

* Replace all persona confirmation messages with a single unified string
* Remove conditional branches that produce different messages
* Ensure all confirm flows use the same toast output

Target message:

```txt
페르조나가 적용되었습니다.
```

---

# Acceptance Criteria

1 All chat types (Character / World / Game) show identical toast message
2 Toast message is exactly: `페르조나가 적용되었습니다.`
3 Persona selection flow works as before (no regression)
4 No conditional message differences remain

---

# Verification

1 Character Chat (new session)

* Open persona modal → select → confirm
* Confirm toast message is unified

2 World Chat (new session)

* Same flow → message 확인

3 Game Chat

* Same flow → message 확인

4 Existing session (all types)

* Change persona → confirm → message 확인

---

# Ticket Size Rule

This ticket modifies only:

* toast message strings in 1–3 files
* no logic or structural changes

---

# AI Implementation Instructions

Before coding:

* Identify all toast message locations related to persona confirmation
* List affected files and functions

After coding:

* List modified files
* Show before/after message changes
* Confirm no remaining inconsistent messages
* Provide verification steps

---

# Important Rule

One ticket should produce:

1 branch
1 pull request

---

# Development Principles

* Maintain UX consistency
* Hide internal implementation differences from users
* Follow ticket-driven development
