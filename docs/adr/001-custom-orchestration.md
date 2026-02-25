# ADR 001: Custom Agent Orchestration

**Status:** Accepted

## Context

The Council of Agents system requires precise control over how agents are managed through deliberation rounds — including anonymous identity assignment, structured turn-taking, cross-agent critique, and aggregation of positions into a collective decision. Existing orchestration frameworks such as LangChain and CrewAI provide high-level abstractions that simplify common patterns but make it difficult to enforce custom constraints at each stage of the pipeline.

## Decision

Build a custom agent orchestration layer rather than adopting LangChain, CrewAI, or a similar framework.

## Reasoning

- **Anonymization requirements:** Agents must not know which LLM provider their peers are using during deliberation. Framework abstractions tend to expose provider identity through naming conventions, logging, and callback structures that are difficult to suppress cleanly.
- **Round structure control:** The deliberation protocol requires explicit, inspectable phases (opening statements, critique rounds, revision, synthesis). Custom code makes these phases first-class concepts rather than workarounds against an opinionated framework.
- **Observability:** A bespoke orchestrator can emit structured events at every decision point, making the deliberation process fully traceable without fighting against framework internals.
- **Learning value:** Building the orchestration layer from scratch provides a deeper understanding of multi-agent coordination patterns that would be obscured by framework abstractions.

## Tradeoffs

| Consideration | Custom Orchestration | Framework (LangChain / CrewAI) |
|---|---|---|
| Development speed | Slower initially | Faster bootstrapping |
| Control over deliberation logic | Full | Limited by abstractions |
| Anonymization enforcement | Straightforward | Requires workarounds |
| Code to maintain | More | Less |
| Dependency surface | Minimal | Large transitive deps |
| Learning outcomes | High | Lower |
