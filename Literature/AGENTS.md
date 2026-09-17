# Literature Review Instructions

## Scope

These instructions apply to literature-review work under this
`Literature/` directory.

Individual paper notes are stored under:

`papers/`

Each paper must have exactly ONE Markdown note containing both:
1. an English structured summary;
2. a Chinese structured summary.

Always follow the template:

`templates/paper_template.md`

---

## Paper Note Creation Rules

When asked to create a literature note from a paper:

1. Read the paper itself before creating the note.
2. Create exactly one Markdown file under `Literature/papers/`.
3. Follow `Literature/templates/paper_template.md`.
4. Complete both the English and Chinese sections.
5. Do not create separate English and Chinese files.
6. Do not omit sections merely because information is unavailable.
7. If information cannot be identified from the paper, write:
   - English: `Not identified in the paper.`
   - Chinese: `论文中未明确说明。`

---

## File Naming

Use:

YYYY_FirstAuthor_ShortTitle.md

Example:

2024_Messager_GlobalPrevalenceNonPerennialRivers.md

Rules:

- Use publication year.
- Use the first author's surname.
- Use a short English title.
- Do not use spaces.
- Do not use Chinese characters in filenames.

---

## Accuracy Rules

Never invent information.

In particular, never guess:

- numerical values;
- thresholds;
- spatial resolution;
- temporal resolution;
- study period;
- dataset names;
- sample size;
- validation results;
- DOI;
- author conclusions.

Preserve important numerical values exactly as reported.

Clearly distinguish between:

1. statements/results reported by the authors;
2. interpretation of the paper;
3. implications for my research.

Do not present interpretation as an author conclusion.

---

## English Summary

Write the English summary directly from the original paper.

Preserve the terminology used in the paper whenever appropriate.

Do not generate the English section by translating the Chinese summary.

Use concise academic English.

---

## Chinese Summary

Write the Chinese summary based directly on the paper.

The purpose is comprehension and later review, not literal translation.

Important technical terminology should retain the original English term
when useful.

Example:

间歇性河流（intermittent river）

非永久性河流（non-perennial river）

水体出现频率（water occurrence）

---

## Current Research Context

### Core Research Question

The current research aims to develop a method for distinguishing
perennial and non-perennial rivers based on river discharge while
accounting for differences in river channel size.

A single global discharge threshold is unlikely to be appropriate,
because the hydrological meaning of a given discharge depends on the
size and geometry of the river channel.

Therefore, the central research question is:

> How should the discharge threshold separating perennial and
> non-perennial rivers vary with river cross-sectional area?

Conceptually, the research seeks to identify a relationship of the form:

Q_threshold = f(A)

where:

- Q_threshold is the discharge threshold associated with flow permanence;
- A is river cross-sectional area;
- f(A) represents how the threshold changes with river channel size.

### Research Approach

The research combines two major sources of information.

#### 1. Hydrological / hydraulic information

CaMa-Flood is used to obtain or analyze river-level information including:

- river discharge;
- river channel geometry;
- river cross-sectional area or variables from which it can be derived.

Each river location can therefore be characterized by quantities such as:

(A_i, Q_i)

where A_i represents river cross-sectional area and Q_i represents
discharge.

#### 2. Observational flow-permanence information

JRC Global Surface Water data are used to determine whether corresponding
river locations exhibit persistent or non-persistent surface water.

JRC-derived information such as water seasonality and occurrence is used
to classify river locations as perennial or non-perennial.

Each usable river observation can therefore conceptually be represented as:

(A_i, Q_i, P_i)

where P_i is the observed perennial/non-perennial status derived from
JRC data.

### Intended Analysis

By comparing modeled river discharge and channel size with
JRC-observed flow permanence across many river locations, the research
aims to identify the boundary between perennial and non-perennial
conditions in the discharge–cross-sectional-area space.

The final relationship should not be assumed to be linear.

Possible formulations, transformations, or hydraulic variables should
be evaluated based on physical reasoning, empirical evidence, and
previous literature rather than assumed in advance.

### Literature Review Priorities

When reviewing literature, pay particular attention to:

1. definitions of perennial, non-perennial, intermittent, and ephemeral rivers;
2. physical controls on flow permanence;
3. relationships between discharge and flow permanence;
4. relationships between river/channel size and discharge;
5. river cross-sectional geometry and hydraulic characteristics;
6. methods for identifying or predicting flow cessation;
7. discharge thresholds or size-dependent thresholds;
8. JRC Global Surface Water and other remote-sensing methods for identifying
   river flow permanence;
9. spatial matching between remotely sensed surface water and river networks;
10. spatial aggregation and scale mismatch;
11. validation datasets and methods;
12. uncertainty and limitations in using surface-water presence as a proxy
    for river flow permanence.

### Important Research Principle

Do not assume that any currently tested threshold or functional form is
correct.

Current parameter values are experimental hypotheses rather than
established conclusions.

Evidence that contradicts the current methodology is as important as
evidence that supports it and must be reported clearly.

---

## Literature Review Roadmap

The literature review is organized into six stages.

This roadmap defines the major evidence categories required for the
research. When processing a paper, determine which stage or stages the
paper contributes to.

A paper may contribute to multiple stages.

Do not force a paper into a stage if it is not relevant.

### Stage 1: Fundamental Concepts and Importance of Perennial and Non-Perennial Rivers

Review the definitions and classification criteria of perennial rivers,
intermittent rivers, ephemeral streams, and non-perennial rivers, as well
as their ecological, hydrological, and water-resource importance.

Key evidence includes:

- definitions and terminology;
- classification systems;
- distinctions among perennial, intermittent, ephemeral, and
  non-perennial rivers;
- temporal definitions of flow permanence;
- ecological importance;
- hydrological importance;
- water-resource implications.

### Stage 2: Existing Methods for Identifying River Flow Permanence

Examine how field observations, gauging stations, remote sensing, river
databases, and hydrological models are currently used to distinguish
perennial from non-perennial rivers, including their strengths,
limitations, and applicable scales.

Key evidence includes:

- field observations;
- stream gauges;
- zero-flow records;
- remote sensing;
- river-network databases;
- hydrological modeling;
- classification algorithms;
- spatial and temporal scales;
- validation methods;
- uncertainty and limitations.

### Stage 3: Discharge-Threshold Methods in Hydrological Models

Investigate how simulated discharge and discharge thresholds are used
to classify river permanence, focusing on the values, theoretical or
empirical basis, and sensitivity of fixed thresholds.

Key evidence includes:

- discharge thresholds;
- zero-flow definitions;
- low-flow thresholds;
- fixed versus variable thresholds;
- theoretical justification;
- empirical calibration;
- threshold sensitivity;
- model dependence.

### Stage 4: Relationships Between Channel Geometry and Flow Permanence

Review studies on how channel width, depth, cross-sectional area, slope,
roughness, and hydraulic radius affect discharge, water depth, flow
velocity, hydraulic connectivity, and river drying.

This stage is particularly important to the central research question
Q_threshold = f(A).

Key evidence includes:

- channel width;
- channel depth;
- cross-sectional area;
- hydraulic radius;
- channel slope;
- roughness;
- hydraulic geometry;
- discharge–geometry relationships;
- flow velocity;
- water depth;
- hydraulic connectivity;
- flow cessation;
- river drying.

### Stage 5: Channel Geometry and Discharge Simulation in Global Hydrological Models

Study the original papers and technical documentation of models such as
CaMa-Flood and H08 to understand how channel geometry is parameterized,
how discharge is calculated, what outputs are produced, and how very
low-flow or dry-channel conditions are handled.

Key evidence includes:

- CaMa-Flood;
- H08;
- river routing;
- channel parameterization;
- channel width and depth;
- cross-sectional area;
- discharge calculation;
- model outputs;
- low-flow treatment;
- dry-channel treatment;
- assumptions and limitations.

For model-specific technical claims, prioritize original model papers
and official technical documentation over secondary descriptions.

### Stage 6: Application of JRC Global Surface Water to River Permanence Identification

Review the definitions, accuracy, and applications of JRC Global Surface
Water products such as Seasonality and Occurrence, with particular
attention to spatial aggregation and the difference between remotely
sensed water presence and actual flowing-water permanence.

Key evidence includes:

- JRC Global Surface Water;
- Seasonality;
- Occurrence;
- Landsat-based water detection;
- product accuracy;
- spatial resolution;
- temporal coverage;
- spatial aggregation;
- river-network matching;
- narrow-river detection;
- mixed pixels;
- water presence versus flowing water;
- disconnected pools;
- limitations for flow-permanence classification.

---

## Roadmap Classification Rules

For every individual paper note, identify:

- **Primary Stage:** the stage to which the paper contributes most directly;
- **Secondary Stage(s):** other stages to which it provides meaningful evidence;
- **Contribution:** what specific question or evidence gap the paper helps address.

A paper may contribute to multiple stages.

Stage assignment must be based on the actual content of the paper rather
than title or keywords alone.

---

## Research-Relevance Analysis

Pay particular attention to information related to:

- perennial rivers;
- non-perennial rivers;
- intermittent rivers;
- ephemeral streams;
- flow permanence;
- river seasonality;
- surface-water occurrence;
- JRC Global Surface Water;
- HydroRIVERS;
- river-network datasets;
- CaMa-Flood;
- discharge;
- river width;
- river cross-sectional area;
- spatial aggregation;
- classification thresholds;
- validation datasets;
- validation methodology.

When relevant, explain specifically how the paper could inform the
methodology, parameter selection, validation, or interpretation of the
current research.

Do not force a connection when the paper is not directly relevant.

---

## Evidence

For important claims, numerical results, definitions, thresholds, and
methodological decisions, record the relevant page number whenever
possible.

Short quotations may be recorded under:

Important Evidence | 重要证据

Do not copy unnecessarily long passages.

---

## Existing Notes

Do not overwrite or substantially modify an existing literature note
unless explicitly asked.

If a note for the same paper appears to already exist, report it before
creating a duplicate.

---

## Review Documents

Files under:

Literature/reviews/

are synthesis documents across multiple papers.

Do not treat them as individual paper summaries.

When creating or updating a review, base conclusions on the individual
paper notes and clearly identify disagreements, common findings,
methodological differences, and research gaps across papers.