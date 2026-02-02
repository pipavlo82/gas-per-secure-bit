# Feedback-loop failures under scaling

## Summary

As protocols scale, new scarce resources are introduced alongside existing ones.
If such resources are not explicitly tracked and incorporated into a feedback loop,
the system tends to converge to pathological equilibria.

This document describes a general class of failures caused by missing control variables
in protocol design, independent of any specific mechanism or proposal.

---

## General failure pattern

A recurring pattern can be observed across protocol layers:

- A protocol introduces a new resource R₂ in addition to an existing resource R₁.
- Demand elasticity between R₁ and R₂ is unknown or unstable.
- Pricing, limits, or semantics do not directly regulate long-term consumption of R₂.
- Under scaling, equilibrium shifts toward:
  - underutilization of R₂, or
  - dominance of R₂ that crowds out R₁.

This is not an implementation bug; it is a control-theoretic failure.

---

## Semantic resources

Not all scarce resources are physical (gas, bytes, storage).
Some resources are semantic in nature.

In cryptographic verification, the scarce resource is meaning:
the binding between a cryptographic statement and its intended verification context.

If verification context is underspecified, cryptographic security may exist
while semantic correctness collapses under scaling.

---

## Semantic replay (“wormholes”)

A characteristic failure mode is semantic replay across verification surfaces:

- the same cryptographic artifact is accepted in multiple contexts
- gas is paid and verification succeeds
- but the meaning of what was verified differs across surfaces

This represents a semantic analogue of resource mispricing.

---

## Control variables

The root cause in all observed cases is the absence of an explicit control variable
that stabilizes the resource under scaling.

In semantic verification, such a control variable must bind:

- domain or lane identifier
- verification surface
- verifier identity
- algorithm identifier (including hash/XOF choices)
- payload

Making this binding explicit prevents silent drift across contexts.

---

## Relation to metrics

Cost metrics without semantic normalization are insufficient.
Meaningful comparison requires normalizing cost by delivered security
under a specific semantic lane.

This motivates surface- and lane-aware metrics (e.g., gas per delivered security bit).

---

## Scope

This document describes a class of failures, not a specific solution.
It is intended as a conceptual framework for protocol design discussions.
