# Codex Guidance

Codex must follow `docs/llm-design-principles.md` for all code changes.

## Required behavior

1. Prefer designs that reduce complexity for future maintainers.
2. Separate logic into:
- pure calculations
- effectful actions at boundaries
3. Keep module interfaces small and clear.
4. Hide internal complexity inside modules, not at call sites.
5. Avoid introducing state duplication or order-dependent logic when not necessary.
6. Keep comments focused on intent, invariants, and non-obvious tradeoffs.

## PR/change checklist

- Complexity reduced or kept flat.
- Abstractions deepened (or at least not made shallower).
- Side effects isolated.
- Naming reflects domain concepts.
- No unnecessary new special cases.

If these are not satisfied, redesign before implementation.

