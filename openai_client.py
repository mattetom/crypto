import logging
import os
import openai
import json
from typing import Dict

openai.api_key = os.getenv("OPENAI_API_KEY")

def call_openai_market_analysis(prompt: str) -> Dict:
    response = openai.responses.create(
        model="gpt-4o-2024-08-06",
        input=[
            {"role": "user", "content": prompt}
        ],
        text={
        "format": {
            "type": "json_schema",
            "name": "analyze_market",
            "schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["long", "short", "wait"]
                    },
                    "next_check_minutes": {
                        "type": "integer"
                    },
                    "reason": {
                        "type": "string"
                    },
                    "take_profit_pct": {
                        "type": "number"
                    },
                    "stop_loss_pct": {
                        "type": "number"
                    },
                    "risk_mode": {
                        "type": "string",
                        "enum": ["standard", "trailing"]
                    }
                },
                "required": ["action", "next_check_minutes", "reason", "take_profit_pct", "stop_loss_pct", "risk_mode"],
                "additionalProperties": False
            },
            "strict": True
        }
    }
    )

    actionToBeDone = json.loads(response.output_text)
    logging.info(f"OpenAI response: {actionToBeDone}")
    return {
        "decision": actionToBeDone,
        "tokens": response.usage.total_tokens
    }
