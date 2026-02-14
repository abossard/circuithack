# LLM Design Principles

This repository requires all AI-generated changes to follow:
- *Grokking Simplicity* (Eric Normand)
- *A Philosophy of Software Design* (John Ousterhout)

## Non-negotiable rules

1. Reduce overall complexity, not just line count.
2. Keep pure logic separate from side effects.
3. Prefer deep modules with simple, stable interfaces.
4. Avoid temporal coupling and "do A then B then C" designs when a single abstraction can own it.
5. Make data flow explicit (inputs, outputs, invariants).
6. Keep effects at boundaries (I/O, network, filesystem, process, hardware).
7. Name things by domain meaning, not mechanism.
8. Add comments for intent/invariants, not for obvious syntax.
9. Do not duplicate logic; extract or centralize shared behavior.
10. If a change adds incidental complexity, revise design before implementation.

## Grokking Simplicity mapping

- `Data`: domain facts and structures.
- `Calculations`: deterministic transforms (no side effects).
- `Actions`: effectful operations.

Required shape:
- Push business logic into calculations.
- Keep actions thin and composable.
- Pass data into calculations; return new data out.

## Philosophy of Software Design mapping

- Design for low cognitive load for future readers.
- Hide complexity behind clear abstractions.
- Keep APIs small and intention-revealing.
- Eliminate special cases where possible.
- Prefer one coherent abstraction over many shallow helpers.

## AI self-check before finishing

1. What complexity was removed?
2. Which module now owns this complexity?
3. What logic is pure vs effectful?
4. Are interfaces simpler than before?
5. Are invariants obvious and documented where needed?

If any answer is weak, redesign before finalizing.

