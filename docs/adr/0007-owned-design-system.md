# ADR-007: Owned Design System on shadcn/Base UI Conventions

- Status: Accepted
- Date: 2026-09-08

## Context

The starter needs an enterprise UI foundation that is accessible, composable and highly customizable without coupling product code to a closed component-library API.

shadcn/ui treats the top-level component source as application-owned code rather than a conventional black-box package. In July 2026, shadcn made Base UI the default primitive foundation for new projects.

## Decision

Create `packages/ui` as the owned design-system package.

- Base UI provides headless behavior and accessibility primitives where behavior is non-trivial.
- Component APIs follow shadcn-style composition and variant conventions.
- Tailwind CSS v4 and semantic CSS variables provide styling and design tokens.
- Product features consume `@cpxlabs-admin/ui`; they do not import Base UI directly.
- Design-system source remains editable in the repository.

## Token layers

```text
primitive values
    ↓
semantic CSS variables
    ↓
Tailwind theme aliases
    ↓
owned components
    ↓
application features
```

Semantic tokens include background, foreground, card, primary, secondary, muted, accent, destructive, border, input, ring, success and warning.

## Guardrails

1. Feature code must not introduce arbitrary brand hex values when an appropriate semantic token exists.
2. Behavioral primitives such as dialogs, menus and comboboxes should use Base UI instead of bespoke focus/keyboard logic.
3. `packages/ui` must not depend on business features.
4. Accessibility semantics belong in the component implementation, not repeated by every consumer.
5. Dark mode is token-driven and may be activated without changing feature components.

## Consequences

- application teams own their UI implementation and can customize it deeply;
- Base UI can evolve behind our public component APIs;
- Tailwind utility usage remains consistent with semantic tokens;
- feature code becomes visually and behaviorally more uniform;
- the starter can later expose a shadcn registry without changing the application architecture.
