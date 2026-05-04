# Conversation Strategy: Managing AI Context

How you talk to an agent is just as important as the code you write. This document explains the best practices for managing your conversations to prevent "AI Drift" and hallucinations.

## 1. The "Modular Chat" Principle
**Rule**: One Task = One Conversation.
*   **Why?**: Every LLM has a "Context Window." As a chat gets longer, the AI has to "summarize" or "forget" older parts of the conversation. This leads to the agent ignoring rules or forgetting file paths.
*   **When to open a new chat**:
    *   When moving to a new Medallion layer (e.g., from Landing to Raw).
    *   When switching personas (e.g., from Architect to Engineer).
    *   After a successful "Big Win" (e.g., "The API extraction is working! Let's start a new chat for the dbt models.").

## 2. The "Grounding" Prompt
Every new chat should start with a "Reset and Ground" prompt. This ensures the agent isn't just guessing.
*   **Essential Elements**:
    1.  **Persona**: Tell the agent which file in `.agents/personas/` to adopt.
    2.  **Goal**: Point to the PRD (`.agents/rules/00-product-vision.md`).
    3.  **State**: Tell the agent to "Review the current state of the `[folder_name]` directory."

## 3. Handling "Multi-Agent" Workflows
If you need an Architect to design and an Engineer to build:
1.  **Chat A (Architect)**: Get the plan and the design. Save them to an ADR or the Implementation Plan.
2.  **Close Chat A**.
3.  **Chat B (Engineer)**: Point the new agent to the plan created in Chat A. This keeps the implementation chat clean and focused.

## 4. The "Audit" Pattern
If you've been working in a chat for a long time and the agent starts making small mistakes:
*   **Action**: Stop. Copy the current code/plan. Open a **New Chat**. 
*   **Prompt**: "Here is our current plan and code. We are moving to the implementation phase. Act as [Persona] and continue."

---
*Created by **Antigravity** — Architectural Conscience*
