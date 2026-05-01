# financial-analyst-agent

## 1. Agent Name

**financial-analyst-agent**

---

## 2. Agent Purpose

The purpose of this agent is to demonstrate **basic agent development with tool usage** focused on simple financial data and calculations.

This agent is designed to:
- interact with the user about an available portfolio of stocks,
- retrieve structured market information via tools,
- compute the Return on Investment (ROI) for given trade scenarios,
- reason about and explain the financial data in natural language.

This description serves as a **technical task specification for the agent's system prompt**.

> **Educational focus:**  
> This agent operates on a small, in-memory catalog of example stocks.  
> It is intentionally simplified and does not represent a complete or production-ready trading algorithm or real-time market data fetcher.

---

## 3. Agent Tools

This agent uses **three tools**, each illustrating a different level of data preparation and action.

### 3.1 `list_stocks`

**Purpose:**  
Provides an overview of all available stocks in the in-memory catalog.

**Output includes:**
- stock ticker,
- company name,
- number of metadata fields.

**Design principle:**  
The tool returns **fully prepared metadata**, allowing the agent to immediately reason about the available portfolio.

---

### 3.2 `describe_stock(ticker)`

**Purpose:**  
Provides detailed information about a single stock.

**Input:**
- `ticker` – exact or best-effort ticker symbol to describe.

**Output includes:**
- ticker,
- company,
- sector,
- current simulated price,
- short text description,
- one example metadata row.

**Design principle:**  
The tool summarizes the stock instead of exposing raw or excessive data. It supplies concise, structured facts for the agent to interpret.

---

### 3.3 `calculate_roi(buy_price, sell_price)`

**Purpose:**  
Returns the calculated Return on Investment (ROI) percentage.

**Input:**
- `buy_price` – The float value representing the purchase price.
- `sell_price` – The float value representing the sale price.

**Output includes:**
- buy and sell prices,
- calculated ROI percentage,
- a note indicating the calculation was performed dynamically.

**Important behavior (explicit requirement):**  
When the user asks the agent to evaluate a trade's profit or return, the agent must call this tool. This demonstrates tool-driven outputs and separation of concerns (mathematical computation vs. agent reasoning).

---

## 4. Tool–Agent Responsibility Split

This agent demonstrates the following fundamental rule:

> **Tools are responsible for data retrieval, preparation, and structuring.**  
> **The agent is responsible for reasoning, explanation, and interpretation.**

Examples:
- Tools retrieve the stock metadata and perform the math for the ROI.
- The agent explains what the company does, interprets if the ROI is a gain or a loss, and presents it professionally to the user.

The agent should not invent structured metadata or attempt to guess mathematical outcomes; it must rely on tool outputs. This separation is a **core expectation** for student agents in this course.

---

## 5. Implementation Details

This agent uses:
- **AG2** `ConversableAgent` for the LLM-powered assistant,
- the `functions=[...]` argument to expose tools to the agent,
- **Chainlit** for the chat UI with **Step visualization** of tool calls.

### AG2 Single-Agent Tool Pattern

This example uses the simpler single-agent tool pattern:
```python
assistant = ConversableAgent(
    name="financial_agent",
    system_message=SYSTEM_PROMPT,
    llm_config=llm_config,
    human_input_mode="NEVER",
    functions=[list_stocks, describe_stock, calculate_roi],
)

User: what stocks are available?

Agent: Here are the stocks currently available in our portfolio:
  | Ticker | Company        |
  |--------|----------------|
  | AAPL   | Apple Inc.     |
  | TSLA   | Tesla Inc.     |
  | MSFT   | Microsoft Corp |

  Let me know if you'd like more details on any of them!

User: describe TSLA

Agent: TSLA represents Tesla Inc. It operates within the Automotive sector. 
The current simulated price for this stock is $202.1.
Would you like to calculate a potential return on investment for this stock?

User: I bought it at 190 and sold at 202.1, what is my ROI?

Agent (calls calculate_roi):
Based on your purchase price of $190 and a selling price of $202.10, your Return on Investment (ROI) is 6.37%. That's a solid profit! Let me know if you have any other trades to analyze.

7. Limitations of This Example
Stocks and metadata are hard-coded and stored in memory.

No real-time API integrations (like Yahoo Finance) are used.

The agent focuses purely on basic calculation and data retrieval for educational purposes.