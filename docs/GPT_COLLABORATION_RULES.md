# GPT Collaboration Rules

This document defines how GPT is used in the Arcanaverse repository.

The goal is to maintain **stable ticket-driven development** without changing structures during implementation.

---

# Core Principle

GPT must not introduce structural changes unless explicitly requested.

Default behavior:

- Follow existing templates
- Produce tickets only
- Do not modify formats
- Do not suggest new repo structures

---

# Allowed GPT Tasks

GPT may perform the following tasks:

1. Create tickets
2. Summarize bug reports
3. Convert analysis into tickets
4. Generate Markdown documents
5. Explain architecture when asked

GPT should NOT modify repository structure unless explicitly requested.

---

# Ticket Generation Mode

When the user requests ticket creation, GPT must:

1. Use the **existing ticket template**
2. Follow the **same formatting**
3. Avoid adding new sections
4. Avoid changing metadata fields

Output must only contain the ticket content.

No structural suggestions.

---

# Ticket Request Format

When requesting ticket generation, the user will provide:

- bug description
- expected behavior
- reproduction steps

Example:

"Create a ticket using the existing template."

GPT must return:

- exactly one ticket
- using the repository ticket template

---

# Template Freeze Rule

Ticket template changes are rare and must be explicitly requested.

GPT must NOT modify ticket templates automatically.

Template modifications require explicit instruction:

"Update the ticket template."

---

# Conversation Modes

GPT operates in three modes.

## 1 Ticket Mode

Used for ticket creation.

GPT must only produce tickets.

No architecture suggestions.

---

## 2 Analysis Mode

Used for debugging.

GPT may analyze code and produce analysis documents.

No structural suggestions.

---

## 3 Architecture Mode

Used only when explicitly requested.

Example request:

"Propose repository architecture improvements."

Only in this mode may GPT suggest structural changes.

---

# Stability Rule

Active development must not change repository structure.

Architecture changes must happen outside active ticket work.

---

# Summary

Default behavior for GPT:

- follow template
- generate tickets
- avoid structural changes