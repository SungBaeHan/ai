# GPT Ticket Mode Rule

When GPT is asked to create a ticket, it must operate in **Ticket Mode**.

## Rules

1. Use the existing ticket template exactly as defined in the repository.
2. Do not add new sections.
3. Do not modify metadata structure.
4. Do not suggest architecture or repository changes.
5. Do not include explanations outside the ticket.

## Output Format

GPT must output **only the ticket markdown**.

No additional commentary.

## Scope

Ticket Mode is used when the user asks:

- "Create a ticket"
- "Generate a bug ticket"
- "Create a task"
- "Create a feature ticket"

## Non-Ticket Requests

If the user explicitly asks for:

- architecture discussion
- repository structure changes
- template modification

then GPT may exit Ticket Mode.

Otherwise, GPT must remain in Ticket Mode.