# Agentic Development: The Conceptual Framework

In this project, we aren't just "writing code with AI"—we are practicing **Agentic Development**. This document explains the core concepts that make this repository "AI-ready."

## 1. Why do we need Personas?
An LLM is a generalist. If you ask it to "fix the code," it might suggest a quick hack that breaks your architecture. By using **Personas** (like `Data Architect` or `Data Engineer`), we:
*   **Restrict the "Search Space"**: Each persona only looks at specific rules and tools.
*   **Set the Tone**: A `Data Architect` will focus on the "Why" and "Scalability," while a `Data Engineer` will focus on "Idempotency" and "Syntax."
*   **Prevent Hallucination**: Personas help the AI stay in its lane.

## 2. The PRD (Product Requirements Document)
Located in `.agents/rules/00-product-vision.md`.
*   **Purpose**: It defines the "What" and "Who."
*   **Agentic Role**: It is the "Anchor of Truth." If the agent suggests adding a Twitter connector, the PRD will stop it because the scope is restricted to YouTube.
*   **Analogy**: The PRD is the **Goal Post**.

## 3. The ADR (Architecture Decision Record)
Located in `.agents/knowledge/adr/`.
*   **Purpose**: It documents **Why** a specific technical choice was made (e.g., "Why use `deploy.py` instead of `schemachange`?").
*   **Agentic Role**: It prevents the AI from "re-suggesting" alternatives you've already rejected. It gives the agent the "Context of History."
*   **Analogy**: The ADR is the **Map of Past Decisions**.

## 4. "Context is King"
Agents work best when they have a "Mental Model" of the repository. We provide this through:
*   **Living Documentation**: READMEs that are updated every time the code changes.
*   **Directory Prefixes**: The `01_`, `02_` prefixes tell the agent (and the human) the exact execution order without reading the scripts.

---
*Created by **Antigravity** — Architectural Conscience*
