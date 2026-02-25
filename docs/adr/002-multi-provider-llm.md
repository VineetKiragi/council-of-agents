# ADR 002: Multi-Provider LLM Strategy

**Status:** Accepted

## Context

A deliberation system is only as useful as the diversity of perspectives its agents bring. Using a single LLM provider means all agents share the same underlying training distribution, RLHF biases, and stylistic tendencies — reducing the deliberation to a form of ensemble prompting rather than genuine multi-perspective debate. The goal of Council of Agents is to surface meaningful disagreement and complementary reasoning across agents.

## Decision

Integrate multiple LLM providers — Anthropic (Claude), OpenAI (GPT), and Google (Gemini) — through a common adapter interface, with each provider capable of populating one or more agent seats in a deliberation session.

## Reasoning

- **Bias mitigation:** Different providers exhibit different reasoning styles, knowledge cutoffs, and value alignments. Using multiple providers reduces the risk that the collective output simply reflects one model's biases.
- **Richer deliberation:** Observed differences in how Claude, GPT, and Gemini approach argumentation, hedging, and synthesis produce more varied and interesting agent positions than single-provider ensembles.
- **Resilience:** If one provider's API is unavailable or rate-limited, sessions can continue with agents from the remaining providers.
- **Provider-agnostic design:** Building an adapter layer forces a clean separation between agent behaviour and model implementation, which is good architectural practice regardless of the provider count.

## Tradeoffs

| Consideration | Multi-Provider | Single Provider |
|---|---|---|
| Perspective diversity | High | Low |
| Single-model bias | Mitigated | Present |
| Adapter complexity | Higher | Minimal |
| API credential management | Three keys required | One key |
| Cost surface | Spread across providers | Concentrated |
| Response latency consistency | Variable per provider | Consistent |
| Interesting deliberation outcomes | More likely | Less likely |
