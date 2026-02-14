# GitHub Copilot Instructions

Copilot must follow `docs/llm-design-principles.md`.

Apply these principles from:
- *Grokking Simplicity*
- *A Philosophy of Software Design*

## Rules for suggestions and edits

1. Reduce cognitive load and incidental complexity.
2. Keep business logic pure where possible; isolate side effects.
3. Prefer deep modules with small, intention-revealing interfaces.
4. Avoid temporal coupling and scattered orchestration logic.
5. Avoid duplicated logic and ad hoc special cases.
6. Use names that communicate domain intent.
7. Add comments only for intent/invariants/non-obvious behavior.

## Before final suggestion

- Confirm where complexity is hidden.
- Confirm pure vs effectful boundaries.
- Confirm API surface did not become harder to use.

