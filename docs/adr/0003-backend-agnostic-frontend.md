# ADR-003: Backend-Agnostic Frontend

- Status: Accepted
- Date: 2026-09-08

## Context

The starter must work with greenfield fullstack TypeScript projects and with existing .NET, Python, Java, Node, REST or GraphQL backends.

## Decision

`apps/web` depends on frontend contracts and API adapters, never on a specific backend framework or ORM.

A future `apps/api` may provide a Fastify reference implementation, but it is optional and replaceable.

## Consequences

- features remain portable across backend stacks;
- API client/adapters become explicit boundaries;
- database and ORM code cannot exist in the web application;
- a project may consume only `apps/web` and shared packages;
- backend migrations do not require rewriting feature UI when contracts remain compatible.
