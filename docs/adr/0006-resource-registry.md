# ADR-006: Resource Registry without CRUD Lock-In

- Status: Accepted
- Date: 2026-09-08

## Context

React Admin/Refine-style resource metadata is valuable for navigation, breadcrumbs, permissions and common CRUD screens, but forcing every business operation through a CRUD abstraction damages domain modeling.

## Decision

Introduce a Resource Registry for metadata and discoverability only.

A resource may register routes, labels, navigation metadata and required capabilities. Generic CRUD may use a DataProvider, but non-CRUD workflows are modeled as explicit use cases/mutations.

## Consequences

The registry may drive:

- sidebar/navigation;
- breadcrumbs;
- command palette;
- page metadata;
- permission-aware discoverability;
- generic CRUD scaffolding.

It must not own:

- domain entities;
- workflow state machines;
- business validation;
- arbitrary domain commands;
- backend persistence details.

This preserves React Admin-like productivity without turning the starter into a CRUD framework.
