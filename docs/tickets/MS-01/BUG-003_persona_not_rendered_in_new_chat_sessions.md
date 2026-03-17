# BUG-003 Persona Not Rendered in New Chat Sessions

Persona selection and persona avatar/name are not rendered consistently when entering newly created chat screens.

Example:

BUG-003 Persona Not Rendered in New Chat Sessions

---

# Metadata

Type: BUG  
Severity: major  
Layer: api | usecase | web-html  
Milestone: MS-01_Stabilization

---

# Problem

New chat sessions do not render persona consistently across character chat, world chat, and game chat.

Current behavior:

- Character chat
  - On new chat entry, persona selector is not shown at the top
  - Persona is not shown on the user's right-side messages
- World chat
  - On new chat entry, persona selector is shown
  - Persona is not shown on the user's right-side messages
- Existing chat sessions
  - Previously saved chats can display persona normally in some cases
- Game chat
  - Persona behavior is inconsistent between initial entry and active chat state
  - Persona rendering differs from expected unified behavior across chat types

Expected behavior:

- Every chat screen must show persona selector at the top
- The currently selected persona must be shown on the user's right-side chat messages
- When persona is changed from the top selector, the changed persona must also be reflected in the message area immediately
- Character chat, world chat, and game chat must follow the same persona rendering rule

Impact:

- User cannot reliably identify which persona is currently active
- New chat UX is inconsistent across chat types
- Persona-based immersion and session continuity are degraded
- Persona state may exist internally but fail to bind correctly to UI render state

---

# Context

This bug appears to be related to persona bootstrap / session initialization / message rendering synchronization in new chat entry flows.

Relevant areas to inspect:

- character chat bootstrap
- world chat bootstrap
- game chat bootstrap
- persona selector initialization
- current session persona loading
- message renderer for user-side bubble
- session validation / persona fallback logic

Relevant files:

apps/web-html/chat/character_*.html  
apps/web-html/world/*.html  
apps/web-html/game/*.html  
apps/web-html/js/persona*.js  
apps/web-html/js/chat*.js  
apps/web-html/js/world*.js  
apps/web-html/js/game*.js  
apps/api/routers/...  
apps/api/services/...

Possible API / bootstrap flow:

page entry  
→ bootstrap/init request  
→ session load or new session create  
→ persona list fetch  
→ current persona resolve  
→ UI header render  
→ message render

Architecture rule:

UI bootstrap must not rely on previously cached state only.  
New session entry must explicitly resolve persona state before rendering header and message area.

---

# Scope

Allowed:

- fix persona bootstrap logic for new chat entry
- fix current persona resolution on initial screen load
- fix message renderer so selected persona appears in user message area
- align character/world/game chat persona behavior
- add safe fallback logic when current persona exists but UI state is empty
- adjust frontend request/response handling if current persona field mapping is incorrect

Not allowed:

- database schema changes
- infra changes
- unrelated chat UI redesign
- large refactors of the entire chat architecture
- changes to unrelated session/message/event persistence logic
- adding new persona product features beyond bug fix scope

---

# Strategy

Possible implementation approaches:

- verify whether new session bootstrap returns current persona consistently for all chat types
- verify whether frontend stores resolved persona into a shared current state before first render
- ensure persona selector header and message renderer both consume the same source of truth
- ensure persona change event updates:
  - current persona state
  - header display
  - outgoing user message persona rendering
- compare working existing-chat flow vs broken new-chat flow and normalize initialization order
- check for fallback mismatch such as:
  - persona list loaded but current persona not selected
  - current persona loaded but not propagated to message renderer
  - renderer reading stale cache/sessionStorage/global state

Recommended approach:

1. Trace new session bootstrap for character/world/game chat separately
2. Identify where current persona becomes null or undefined during first render
3. Normalize persona state assignment before chat UI render
4. Reuse one shared resolver for:
   - top persona selector
   - right-side user message persona display
5. Confirm persona change updates both header and message area without reload

---

# Acceptance Criteria

1. Character chat new entry shows persona selector at the top correctly

2. World chat new entry shows persona selector at the top correctly

3. Game chat new entry shows persona selector at the top correctly

4. Selected persona is rendered on the user's right-side chat messages in all chat types

5. Changing persona from the top selector updates chat message persona rendering correctly

6. Existing chat sessions continue to work without regression

7. Persona rendering behavior is consistent across character chat, world chat, and game chat

---

# Verification

1. Start API and web frontend

2. Open character chat from home and enter a new chat session

3. Confirm:
   - top persona selector is visible
   - selected persona is shown on user-side message area

4. Open world chat from home and enter a new chat session

5. Confirm:
   - top persona selector is visible
   - selected persona is shown on user-side message area

6. Open game chat from home and enter a new chat session

7. Confirm:
   - top persona selector is visible
   - selected persona is shown on user-side message area

8. Change persona from the top selector on each chat type

9. Send a new message and confirm changed persona is reflected immediately

10. Re-open an existing chat session and confirm no regression

11. Inspect network / console logs and confirm current persona resolution succeeds during initial bootstrap

---

# Ticket Size Rule

Tickets should remain **small and focused**.

A single ticket should typically modify:

- 1–3 files
- a single logical change

If the fix requires separate corrections for:
- bootstrap response mapping
- frontend shared persona renderer
- chat-type specific initialization

then split follow-up work into sub tickets.

---

# AI Implementation Instructions

Before coding the AI must provide:

- root cause analysis
- files to modify
- implementation plan

After coding the AI must provide:

- files changed
- summary of changes
- verification steps
- potential risks

---

# Important Rule

One ticket should produce:

1 branch  
1 pull request

---

# Development Principles

Arcanaverse follows **AI-native development**.

Principles:

- SSOT
- Architecture-first development
- Ticket-driven development
- AI-assisted implementation
