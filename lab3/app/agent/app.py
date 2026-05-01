import os
import json
from typing import Annotated, Dict

import chainlit as cl
from autogen import ConversableAgent
from autogen.events.agent_events import ExecuteFunctionEvent, ExecutedFunctionEvent

# ---------------------------
#  In-memory example datasets
# ---------------------------

stocks_state: Dict[str, list] = {
    "AAPL": [
        {
            "ticker": "AAPL",
            "company": "Apple Inc.",
            "sector": "Technology",
            "current_price": 175.50,
            "volatility": "Medium"
        }
    ],
    "TSLA": [
        {
            "ticker": "TSLA",
            "company": "Tesla Inc.",
            "sector": "Automotive",
            "current_price": 202.10,
            "volatility": "High"
        }
    ],
    "MSFT": [
        {
            "ticker": "MSFT",
            "company": "Microsoft Corp",
            "sector": "Technology",
            "current_price": 415.20,
            "volatility": "Low"
        }
    ],
}

# ---------------------------
#  Tools (plain functions)
# ---------------------------

def list_stocks() -> Dict:
    """Return all available stocks with basic metadata summary."""
    stocks_info = []
    for ticker, rows in stocks_state.items():
        num_records = len(rows)
        example = rows[0] if num_records > 0 else {}
        num_fields = len(example) if num_records > 0 else 0
        company = example.get("company") if isinstance(example, dict) else None
        
        stocks_info.append(
            {
                "ticker": ticker,
                "company": company,
                "fields": num_fields,
            }
        )
    return {"stocks": stocks_info}

def describe_stock(
    ticker: Annotated[
        str,
        "Ticker symbol of the stock to describe (e.g., AAPL, TSLA). Accepts exact or best-effort titles.",
    ],
) -> Dict:
    """Return concise metadata for a single stock."""
    ticker_upper = ticker.upper()
    if ticker_upper not in stocks_state:
        return {
            "ok": False,
            "error": "stock_not_found",
            "message": (
                f"Stock '{ticker_upper}' not found. "
                f"Available stocks: {', '.join(stocks_state.keys())}."
            ),
        }

    rows = stocks_state[ticker_upper]
    num_records = len(rows)
    example = rows[0] if num_records > 0 else {}
    num_fields = len(example) if num_records > 0 else 0

    description = None
    if example:
        description = (
            f"{example.get('company')} ({example.get('ticker')}) is a company in the "
            f"{example.get('sector')} sector. Its current simulated price is ${example.get('current_price')}."
        )

    return {
        "ok": True,
        "ticker": ticker_upper,
        "company": example.get("company"),
        "sector": example.get("sector"),
        "current_price": example.get("current_price"),
        "description": description,
        "num_fields": num_fields,
        "example_row": example if num_records > 0 else None,
    }

def calculate_roi(
    buy_price: Annotated[float, "The price at which the asset was purchased."],
    sell_price: Annotated[float, "The price at which the asset was sold."],
) -> Dict:
    """Return the Return on Investment (ROI) calculation."""
    if buy_price <= 0:
        return {
            "ok": False,
            "error": "invalid_price",
            "message": "Buy price must be greater than zero."
        }
    
    roi = ((sell_price - buy_price) / buy_price) * 100
    return {
        "ok": True,
        "buy_price": buy_price,
        "sell_price": sell_price,
        "roi_percentage": round(roi, 2),
        "note": "This calculation is performed dynamically by the tool.",
    }

# ---------------------------
#  LLM configuration
# ---------------------------

api_base_url = os.getenv("API_BASE_URL")
api_key = os.getenv("API_KEY")
model = os.getenv("MODEL", "llama3-groq-70b-8192-tool-use-preview")

if not api_key:
    raise RuntimeError(
        "API_KEY is not set. "
        "Set it in your .env file or docker compose environment."
    )

llm_config = {
    "config_list": [
        {
            "model": model,
            "api_key": api_key,
            "base_url": api_base_url,
            "price": [0, 0],
        }
    ],
}

# ---------------------------
#  System prompt
# ---------------------------

SYSTEM_PROMPT = """\
You are a Financial Analyst agent. You work with a small in-memory
catalog of stocks that are already loaded into memory and exposed via tools.

You have the following tools:
- list_stocks: show all available stocks and basic metadata (ticker, company).
- describe_stock: describe a specific stock in more detail, including
  sector, current price, and a short description.
- calculate_roi: calculate the Return on Investment (ROI) given a buy price and a sell price.

Rules:
1) If the user asks what stocks are available or wants an overview, always
   call list_stocks.
2) If the user asks about a specific stock (price, sector, company),
   call describe_stock for that stock.
3) If the user explicitly asks to calculate a return, profit, or ROI for specific
   buy and sell prices, call calculate_roi.
4) For general financial discussion, use the tools to gather
   the structured facts first, then answer in natural language based on the
   tool results.
5) For casual small talk (hello, how are you), answer briefly, but if the
   question concerns the stock catalog or calculations, focus on using the tools.

Always answer in English.
"""

def _format_content(content: object) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, (dict, list, tuple)):
        return json.dumps(content, ensure_ascii=True, indent=2)
    return str(content)

# ---------------------------
#  Chainlit event handlers
# ---------------------------

@cl.on_chat_start
async def on_chat_start():
    """Create the AG2 assistant and store it in the user session."""
    assistant = ConversableAgent(
        name="financial_agent",
        system_message=SYSTEM_PROMPT,
        llm_config=llm_config,
        human_input_mode="NEVER",
        functions=[list_stocks, describe_stock, calculate_roi],
    )

    cl.user_session.set("assistant", assistant)
    
    welcome_msg = (
        "Hello! I am the Financial Analyst agent for this lab.\n\n"
        "I can inspect our small example stock portfolio and calculate trade returns. Try asking:\n"
        "- What stocks are available?\n"
        "- Describe TSLA.\n"
        "- I bought a stock at 150 and sold it at 180, what is my ROI?\n\n"
        "When I use a tool, Chainlit will show the call as an expandable step."
    )
    await cl.Message(content=welcome_msg).send()

@cl.on_message
async def on_message(message: cl.Message):
    """Handle each user message using AG2 async single-agent execution."""
    assistant: ConversableAgent = cl.user_session.get("assistant")

    response = await assistant.a_run(
        message=message.content,
        clear_history=False,
        max_turns=6,
        summary_method="last_msg",
        user_input=False,
    )

    tool_inputs: dict[str, dict[str, str]] = {}

    async for event in response.events:
        if isinstance(event, ExecuteFunctionEvent):
            event_data = event.content
            tool_key = getattr(event_data, "call_id", None) or event_data.func_name
            tool_inputs[tool_key] = {
                "name": event_data.func_name,
                "input": _format_content(event_data.arguments) or "(no arguments)",
            }
            continue

        if not isinstance(event, ExecutedFunctionEvent):
            continue

        event_data = event.content
        tool_key = getattr(event_data, "call_id", None) or event_data.func_name
        step_data = tool_inputs.get(
            tool_key,
            {
                "name": event_data.func_name,
                "input": "(no arguments)",
            },
        )
        async with cl.Step(name=step_data["name"], type="tool") as step:
            step.input = step_data["input"]
            step.output = _format_content(event_data.content)

    summary = await response.summary
    final_text = _format_content(summary)
    await cl.Message(content=final_text).send()