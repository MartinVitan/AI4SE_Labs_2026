---
name: architecture-decision-workflow
description: "Use when analyzing software requirements, proposing and comparing architectural alternatives, explaining architecture trade-offs or implementation scenarios, checking a user's understanding, and drafting or revising an Architecture Decision Record (ADR)."
argument-hint: "Provide requirements, constraints, prior discussion or ADRs, and the decision you need to explore."
---

# Architecture Analysis and ADR Workflow

Use this workflow to help a user move from requirements to an informed architecture decision and a traceable ADR. The skill is architecture-neutral: do not default to a monolith, modular monolith, microservices, or any other style.

## 1. Establish scope and inspect context

1. Read the requirements and any supplied discussions, architecture documents, ADRs, repository guidance, and relevant project files.
2. Follow existing repository conventions for ADR location and format. If no convention exists, ask where the user wants the ADR saved before creating project files.
3. Separate evidence into:
   - **Facts:** explicitly stated requirements, constraints, decisions, or observed repository behavior.
   - **Assumptions:** provisional interpretations needed to explore an option; label them and do not present them as user requirements.
   - **Open questions:** missing information that could change the decision.
4. Do not invent scale, availability targets, performance thresholds, security/compliance obligations, team skills, budget, technologies, or deployment constraints. If they matter, ask or mark them open.
5. Ask focused questions when ambiguity changes the architecture choice. Otherwise proceed with clearly labeled assumptions and explain their effect.

## 2. Explore at least three suitable alternatives

1. Propose at least three materially distinct architectures that fit the known requirements. They need not be a fixed catalog; choose alternatives based on the system.
2. Explain each in comparable terms:
   - runtime and deployment units;
   - ownership of responsibilities and data;
   - communication between parts;
   - how the requirements would be implemented.
3. Compare relevant trade-offs fairly, using consistent criteria where applicable. Consider performance and scalability, availability and failure behavior, security boundaries, maintainability, deployability, operational/development complexity, and cost when supported by context.
4. State conditional properties as conditional. For example, independent scaling, fault isolation, or security benefits are not automatic consequences of an architecture label.
5. Do not present layered and modular organization as mutually exclusive: layers describe technical responsibilities; modules describe functional boundaries. Explain the distinction when relevant.
6. Do not create numeric scores, weights, rankings, or measured claims without user-provided goals and a transparent evaluation basis. If a score matrix would help, ask for criteria and weights or provide an explicitly qualitative comparison instead.

## 3. Explain concrete implementation scenarios

Choose scenarios that expose consequential architectural behavior, not just happy-path diagrams. Follow each scenario across its relevant layers, modules, services, data stores, and external systems. Explain ownership, state transitions, consistency, errors, retries, and user-visible outcomes as appropriate.

For scenarios involving concurrency or external effects, examine relevant cases such as:

- competing requests for the last available resource;
- reservation expiry racing with confirmation;
- payment confirmation arriving late or more than once;
- a service performing an operation while its response is lost;
- failures between a database commit and an external side effect such as email.

Distinguish local database transactions from work involving external systems or independently deployed services. Explain idempotency and compensating actions only where applicable. A modular monolith does not inherently require sagas; use local transactions for changes that share a transactional boundary, and describe compensation only for effects that cannot be rolled back that way.

Keep scenario-specific implementation detail out of the comparison table if it is explained fully in consequences; avoid needless repetition while preserving important risks.

## 4. Check the user's understanding without inferring it

1. Give the user room to explain an architecture or scenario in their own words. Invite a restatement after a substantial explanation or when the user requests learning-oriented guidance.
2. Evaluate only what the user explicitly restates. A question, a request for clarification, or a general acknowledgment is not evidence that the user understands the topic.
3. Confirm accurate parts, gently correct inaccuracies, and identify what remains unclear. Do not attribute assistant explanations, assumptions, or conclusions to the user.
4. If the user does not provide a restatement, say that understanding has not yet been demonstrated rather than filling it in for them. Continue with the requested task without pressuring them.

## 5. Support a transparent decision

1. Present a reasoned recommendation based on stated requirements and relevant trade-offs, or explain why the available information is insufficient to recommend one.
2. Make clear what the user/team is choosing and what is sacrificed or made harder.
3. Let the user decide. Do not treat the assistant's recommendation, a user's interest, or a request to draft an ADR as approval.
4. Record decision status precisely:
   - **Proposed**: recommendation or draft awaiting review.
   - **User-supported**: user explicitly supports the recommendation; this is not necessarily formal team approval.
   - **Accepted**: only when the user explicitly says the authorized decision-makers have accepted it, or the user explicitly declares their own decision final in the relevant context.
   - Use other lifecycle states only when the user or repository convention supports them.
5. If the user selects a different alternative, update the rationale and consequences accordingly; do not defend a prior recommendation as a foregone conclusion.

## 6. Draft and iteratively revise the ADR

Use the repository's ADR template when present. Otherwise use a concise structure appropriate to the decision:

- identifier and title;
- status and date (author/deciders only when known);
- context: problem, relevant facts, requirements, constraints, assumptions, and unknowns;
- one clear decision statement;
- alternatives considered, including relevant advantages, disadvantages, and trade-offs for each;
- rationale tied to known requirements;
- consequences, risks, and difficult implementation concerns;
- assumptions and open questions.

When revising:

1. Read the current ADR and apply the user's requested changes without discarding unrelated content.
2. Keep the three-or-more alternatives visible and compare them fairly.
3. Reduce duplicate explanation between tables and prose, but retain scenario details the user asked to preserve.
4. Do not convert an open question into a decision without user input.
5. Do not claim formal approval based only on support for a recommendation.
6. Inspect the final file for consistency, status accuracy, unsupported claims, and adherence to repository format. Report its path and summarize the material changes.

## 7. Maintain accurate conversation notes

Keep concise chronological notes during multi-turn work, in the conversation or a requested artifact. Record:

- the user's actual questions, constraints, corrections, and explicit summaries;
- the assistant's proposals and explanations;
- each material ADR change and the reason for it;
- the user's explicit response to a recommendation, using the exact level of commitment expressed;
- unresolved questions and what remains unapproved.

Paraphrase faithfully; mark quotations only when text is copied verbatim. Keep user statements separate from assistant analysis. Do not infer opinions, understanding, choices, or approvals. At the end, provide a chronological report when requested, distinguish user contributions from assistant contributions, and note gaps rather than filling them with invented dialogue.

## Completion checklist

- [ ] Requirements are separated into facts, assumptions, and open questions.
- [ ] At least three suitable, materially distinct alternatives are compared fairly.
- [ ] No unsupported metrics, technologies, or constraints were invented.
- [ ] Relevant implementation scenarios and failure cases are explained.
- [ ] User understanding is assessed only from explicit restatements.
- [ ] Recommendation and decision status match what the user actually said.
- [ ] ADR follows repository conventions, avoids needless repetition, and preserves open questions.
- [ ] Conversation notes accurately distinguish user statements from assistant contributions.
