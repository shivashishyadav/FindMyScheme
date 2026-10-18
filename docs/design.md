# FindMyScheme: System Design

Find the government schemes you deserve, in your own language.

This document describes the architecture, data pipeline, user flow, edge cases and build plan for FindMyScheme.

## 1. Goals and principles

**Goal:** Help a person discover which government schemes they may be eligible for, by describing themselves in plain language (text or voice, Hindi / Hinglish / English).

**Core principles**

1. **Eligibility is decided by verified rules, never by an LLM.** Rules are deterministic and testable.
2. **LLMs are used only where they are strong:** understanding user input, drafting rules for human review, and explaining results from verified text.
3. **Human-in-the-loop for data quality.** Nothing becomes "verified" without review.
4. **Honest uncertainty.** The system returns three outcomes (Eligible, Not eligible, Need more info), never a forced yes/no.
5. **Minimal user data.** No Aadhaar, phone numbers or other sensitive identifiers are requested or stored.

## 2. System overview

The system has two halves connected by a database.

- **Offline half (background):** collects, cleans and structures scheme data. Users never see this.
- **Online half (live):** takes user input, matches it against rules, explains the result.

```
 [OFFLINE: data preparation]                   [ONLINE: user flow]

 myScheme / Guideline PDFs                     User (text / voice)
        |                                            |
        v                                            v
 1. Collector                                6. Input Understanding (LLM)
        |                                            |
        v                                            v
 2. Cleaner                                  7. User Profile (structured)
        |                                            |
        v                                            v
 3. Structurer (LLM drafts rules)            8. Rule Engine (decides eligibility)
        |                                            |
        v                                            v
 4. Validator (human review)                 9. Ranker
        |                                            |
        v                                            v
 5. DATABASE  <------------------------------ 10. Explainer (RAG + LLM)
   (schemes, rules, docs, text chunks)               |
                                                     v
                                              11. Final answer + disclaimer
```

## 3. Offline pipeline

| Step | What happens |
|---|---|
| **1. Collection** | Fetch data for a small set of popular schemes (name, ministry, eligibility text, benefits, documents, apply process, source URL). Ministry guideline PDFs are added manually. Requests are rate-limited, and the site's robots.txt and terms are respected. |
| **2. Cleaning** | Strip HTML, remove duplicates, normalise formats (e.g. "Rs 2.5 lakh", "2,50,000", "2.5L" become one standard value). |
| **3. Structuring** | Each scheme's eligibility is stored in two forms: the original text (for explanation) and structured rules (for matching). An LLM drafts the rules. |
| **4. Validation** | A reviewer compares the original text with the extracted rules and marks the scheme verified. Unverified schemes are never shown as "definitely eligible". |
| **5. Storage** | Structured data goes to the relational database. Text chunks go to a vector store for RAG. |
| **6. Refresh** | The pipeline runs periodically. New data is diffed against old data. If something eligibility-related changed, the scheme is marked `review_needed`. Rules never go live automatically in the early versions. |

### Supported rule fields (initial)

age, occupation, annual income, state, gender, social category, land ownership, and "already receiving another scheme". Anything outside this list is shown as "check the official portal".

## 4. Data model (concept level)

| Entity | Contents |
|---|---|
| **Scheme** | name, ministry, level (central/state), short description, source URL, last_updated, status (draft / verified / review_needed) |
| **EligibilityRule** | scheme, field, operator, value, source text snippet |
| **RuleVersion** | history of rule changes for audit and rollback; verified_by, verified_at |
| **Benefit** | what the scheme gives (cash, subsidy, insurance, etc.) |
| **RequiredDocument** | documents needed to apply |
| **ApplyStep** | where and how to apply |
| **SourceSnapshot** | raw fetched content, fetched_at, content hash |
| **TextChunk** | scheme text split for RAG, with embedding |
| **SearchSession** | what the user asked and what result they got (optional, privacy-minimal) |
| **Feedback** | "this result was right / wrong" reports |

## 5. Online flow

1. **User input.** Text or voice. Voice is converted to text first.
2. **Understanding (LLM).** Extract details such as age, occupation, state, land, income, category. The LLM does not decide eligibility.
3. **Profile.** Details are stored in a structured profile. Anything not mentioned stays `unknown`.
4. **Confirmation.** The system shows what it understood: "I understood this, is it correct?"
5. **Gap check.** Find which missing details matter for which schemes. Ask at most 2-3 questions at a time.
6. **Rule matching.** Each scheme gets one of three results:
   - **Eligible:** all rules pass.
   - **Not eligible:** at least one rule fails, and which one is recorded.
   - **Need more info:** some required detail is missing.
7. **Ranking.** Eligible schemes are ordered by benefit, ease of applying and relevance.
8. **Explanation (RAG).** For each scheme, retrieve its verified text and let the LLM explain only from that text: benefits, documents, how to apply.
9. **Final answer.** Plain language, with the reason for each match, documents, apply link, source, last updated date, and a disclaimer to confirm on the official portal.

## 6. Edge cases

| Situation | Behaviour |
|---|---|
| Very little information given | Show "Need more info" schemes and ask 2-3 key questions |
| Contradictory details (e.g. age 12 and landowner farmer) | Ask the user to confirm; do not guess |
| State not given | Ask for state first, since state schemes differ |
| No scheme matches | Say so clearly; show near-misses ("eligible if income were slightly lower") |
| Question not answerable from stored data | Say "I don't have this information"; do not guess |
| Scheme data stale or `review_needed` | Show a warning or hide the scheme |
| Hindi / Hinglish / mixed input | LLM normalises; the profile is always in one standard format |
| Voice transcription may be wrong | Show the understood details and ask for confirmation |
| Sensitive info (Aadhaar, phone) | Never ask, never store |
| Out-of-scope question | Politely decline |
| Two schemes cannot be combined | A `conflict` field in rules; tell the user |
| Source site down or fetch fails | Keep serving last verified data; retry the pipeline |

## 7. Where AI/ML is used

| Place | Technique | Why |
|---|---|---|
| Voice to text | Speech recognition | Hindi voice input |
| Extracting user details | LLM / NER | Free text to structured profile |
| Drafting rules | LLM | First draft from eligibility text |
| Finding relevant scheme text | Embeddings + vector search | RAG retrieval |
| Writing explanations | LLM | Plain-language answers |
| **Deciding eligibility** | **No ML. Rules only.** | Deterministic and testable |
| Ranking (later) | Simple scoring, then ML | Better suggestions |

## 8. Trust and safety rules

1. Eligibility only from verified rules.
2. Every answer shows a source link and last updated date.
3. The LLM answers only from the retrieved text.
4. A disclaimer is always shown.
5. Collect the minimum user data.
6. A feedback button feeds wrong results back into the review queue.

## 9. Path to production (automation without losing accuracy)

The aim is to reduce human effort, not remove humans.

**Automatic validation:** format checks, logic checks (min age is not above max age), and a check that every extracted value actually appears in the source text.

**Cross-verification:** run extraction multiple times and compare; compare two sources (portal vs guideline PDF); use a second LLM as a checker.

**Risk tiers**

| Tier | Example | Action |
|---|---|---|
| Low | Typo, link or date change; rules unchanged | Auto-approve, logged |
| Medium | Rules same, minor field change | Auto-approve, sampled audit |
| High | Income limit, age or eligibility condition changed | Human review required |
| Critical | Scheme closed, large change, model disagreement | Hide scheme and review |

**Change detection:** diff old vs new text; only schemes with eligibility-related changes enter the pipeline.

**Fast review UI:** side-by-side original text and rules, changed parts highlighted, one-click approve/reject, priority queue, bulk approve for low-risk items.

**Safety nets:** golden test set, versioning with rollback, canary release, random audits, user feedback loop, monitoring and alerts, audit trail.

## 10. Project structure

```
findmyscheme/
├── config/          # settings, urls
├── schemes/         # scheme data, rules, admin
├── engine/          # eligibility rule engine (pure Python, no Django models)
├── ingestion/       # collector, cleaner, structurer, change detection
├── assistant/       # LLM, profile extraction, RAG
├── web/             # pages, forms, templates
├── tests/
└── docs/            # this document
```

The `engine` is kept independent of Django so it can be tested on its own.

## 11. Build plan

### Phase 1: Foundation (rules-based MVP)
- **Unit 0:** Project setup
- **Unit 1:** Scheme models
- **Unit 2:** Eligibility rule model and versions
- **Unit 3:** Admin panel as a reviewer tool
- **Unit 4:** Seed data (5 schemes)
- **Unit 5:** Rule engine with three-way output
- **Unit 6:** Web form and result page (tag `v0.1`)
- **Unit 7:** Golden test set and CI

### Phase 2: Data pipeline
- **Unit 8:** Collector and raw snapshots
- **Unit 9:** Cleaner
- **Unit 10:** LLM structurer (draft rules)
- **Unit 11:** Change detection and risk tiers (tag `v0.2`)

### Phase 3: AI user experience
- **Unit 12:** Free text to profile
- **Unit 13:** Missing-info questions
- **Unit 14:** RAG explanation (tag `v0.3`)

### Phase 4: Polish
- **Unit 15:** Feedback and search history
- **Unit 16:** Hindi UI and voice input
- **Unit 17:** Scheduled refresh, logging, alerts
- **Unit 18:** Docker and deployment (tag `v1.0`)

## 12. Git workflow

- `main` is always working.
- One branch per unit, e.g. `unit-01-schemes-models`.
- Small commits with prefixes: `feat:`, `fix:`, `test:`, `docs:`, `chore:`.
- Merge via pull request, then tag releases (`v0.1`, `v0.2`, ...).
- Update the README at the end of every unit.

## 13. Disclaimer

FindMyScheme is an informational tool. Scheme rules change, so final eligibility must always be confirmed on the official government portal.