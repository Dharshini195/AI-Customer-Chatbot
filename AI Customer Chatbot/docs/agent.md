# 🧠 Agent Logic

The core function is `agent_support()`.

## Flow

1. Build system prompt
2. Add conversation history
3. Send to LLM
4. Parse JSON response
5. Execute tool if needed
6. Loop until final answer

## Key Concept

The agent works in a loop:
- Think
- Act (tool)
- Observe
- Repeat