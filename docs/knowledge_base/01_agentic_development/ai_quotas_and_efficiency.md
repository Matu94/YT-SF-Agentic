# AI Quotas & Token Efficiency: Managing the "Invisible Budget"

In agentic development, your AI Service Quota is a critical resource. If you "hit the wall" on your message limit, your development cycle stops. This document explains how to manage your AI credits effectively.

## 1. How Quotas Work: The "Rolling Window"
Most high-tier AI models (like Gemini 3.1 or others) do not use a "Daily Reset." Instead, they use a **Rolling Window** (typically 3 to 5 hours).
*   **The Concept**: Your quota isn't "refilled" at midnight. Instead, every message you sent "expires" X hours after you sent it. 
*   **The "Wall"**: If you send 50 messages in 1 hour, you might hit your limit. You will then have to wait until those 50 messages "age out" of the window before you can send more.
*   **Strategy**: Space out your complex architectural brainstorming sessions. If you feel yourself "rapid-firing" small questions, stop and group them.

## 2. Token Weight: Why Long Chats are "Expensive"
Every time you send a message, the **entire chat history** is sent to the AI again so it can "remember" what we've done.
*   **The Math**: 
    *   Message 1: 500 tokens.
    *   Message 2: 500 tokens + History of Message 1 = 1,000 tokens.
    *   Message 10: 5,000+ tokens.
*   **The Consequence**: Long chats don't just get slower; they consume more "compute power" per message. In some systems, this can lead to faster quota depletion or reduced reasoning quality.
*   **The "Modular Chat" Fix**: This is why we advocate for opening a **New Chat Window** for every new task. It "resets" the token weight to zero.

## 3. The "Batching" Technique
To get the most "value" out of a single message, use **Batching**:
*   **Inefficient**: 
    1. "Create table A." 
    2. "Now create table B." 
    3. "Now add a grant." (3 messages)
*   **Efficient**: 
    "Create tables A and B, then provide the SQL to grant USAGE on both to the LOAD_ROLE." (1 message)

## 4. When to Use "Drafting Mode"
If you are experimenting with code and expect to fail/debug multiple times:
1.  Ask the AI for a **Draft** or **Plan** first.
2.  Review it yourself manually.
3.  Only ask the AI to "Execute/Write" once the plan looks 90% correct.
*   This prevents wasting 5-10 messages on simple logic fixes that you could have spotted in a plan.

## 5. The "Audit" Warning
If you see the AI starts to repeat itself or "hallucinate" paths that don't exist, it's often a sign that the **Context Window is too full**. 
*   **Action**: Stop the chat. Copy the current working code. Start a **New Chat** with the prompt: *"We are continuing work on X. Here is the current state: [Code]. Ignore all previous history."*

---
*Created by **Antigravity** — Architectural Conscience*
