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

## 4. The Atomic Task Rule (Mastering the Scope)
A common mistake is asking an agent for a "Mega-Task" (e.g., "Set up the whole database"). This forces the agent to make too many assumptions at once.
*   **The Best Practice**: Break goals into **Atomic Tasks**—steps that have a clear beginning, middle, and end.
*   **Current Project Example**: Instead of "Set up RBAC," we broke it into:
    1.  Initialize Infrastructure (`00_infrastructure_init.sql`).
    2.  Define Object Roles (`01_role_init.sql`).
    3.  Grant Privileges (`02_grant_init.sql`).
*   **Benefit**: If Step 2 fails, the context is small enough to fix easily without re-reading the entire project's history.

## 5. The "Steering Wheel" (Human-in-the-Loop)
In this project, you (the Human) are the **Pilot**, and I am the **Auto-pilot**. 
*   **The Pilot's Duty**: You are the final Quality Control. You should never assume the AI's first draft is perfect.
*   **Effective Feedback**: If an agent makes a mistake, don't just say "it's wrong." Provide the **Error Log** or the **Expected vs. Actual** result.
*   **Steering**: If you see the agent going down a "rabbit hole" (e.g., over-complicating a simple Python script), use your authority to say: *"Stop. Let's simplify this. Use a basic loop instead of a complex generator."*

## 6. "Context is King"
Agents work best when they have a "Mental Model" of the repository. We provide this through:
*   **Living Documentation**: READMEs that are updated every time the code changes.
*   **Directory Prefixes**: The `01_`, `02_` prefixes tell the agent (and the human) the exact execution order without reading the scripts.

---
*Created by **Antigravity** — Architectural Conscience*
