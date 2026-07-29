# EduAgent LK — Viva Notes

## Project problem

Grade 9–10 English teachers need significant preparation time for lesson plans, activities, exercises, answer keys and quality checking. EduAgent LK automates a first draft while grounding it in a Sri Lankan English-teaching corpus and retaining teacher judgement.

## Why it is agentic

The application does not send one prompt to one model. The Orchestrator assigns different responsibilities to specialised agents, agents exchange typed messages, the Curriculum Agent uses a retrieval tool, and the Review Agent can cause another planning action.

## Patterns

1. **Router:** selects lesson plan, worksheet, quiz or revision-paper route.
2. **Planning/task decomposition:** the output is divided into objectives, teaching, practice, assessment and answers.
3. **Tool use:** the Curriculum Agent calls semantic retrieval.
4. **Reflection:** the Review Agent scores the draft and sends revision instructions.
5. **Orchestrator–worker:** the central controller manages workers and the bounded loop.

## Agent-to-agent communication

Pydantic `AgentMessage` objects include sender, receiver, performative, task ID, timestamp and structured payload. Examples include Curriculum Agent → Lesson Planning Agent and Lesson Planning Agent → Review Agent.

## Why two models

`llama-3.1-8b-instant` is used for low-cost, fast constrained tasks. `openai/gpt-oss-120b` is used for the longer synthesis and revision where stronger reasoning is more useful. Both are configurable and the application does not use one model for all tasks.

## RAG explanation

Documents are loaded, split into 320-word chunks with 55-word overlap, embedded with MiniLM, stored in FAISS and filtered by grade. The top five chunks are passed to the planner. A retry query is used when retrieval is weak.

## Reflection loop

The review JSON contains five 1–5 scores. If any important score is weak, `revision_required` becomes true and the orchestrator sends the instructions back to the planner. The loop is limited to one revision to control cost and latency.

## Limitations to state honestly

PDF extraction may be imperfect, generated teaching material still needs teacher verification, only Grades 9–10 English are supported, and model availability/prices may change.
