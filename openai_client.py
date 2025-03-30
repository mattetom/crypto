import logging
import os
import openai
import json
from typing import Dict

openai.api_key = os.getenv("OPENAI_API_KEY")

function_schema = {
    "name": "analyze_market",
    "description": "Analizza i dati di mercato e suggerisce l'azione da compiere e quando rieseguire l'analisi",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["buy", "sell", "wait"]
            },
            "next_check_minutes": {
                "type": "integer"
            },
            "reason": {
                "type": "string"
            }
        },
        "required": ["action", "next_check_minutes", "reason"]
    }
}

def call_openai_market_analysis(prompt: str) -> Dict:
    response = openai.responses.create(
        model="gpt-4o-mini-2024-07-18",
        temperature=0.2,
        input=[
            {"role": "system", "content": "Sei un esperto di trading crypto."},
            {"role": "user", "content": prompt}
        ],
        text={
        "format": {
            "type": "json_schema",
            "name": "analyze_market",
            "description": "Analizza i dati di mercato e suggerisce l'azione da eventualmente compiere e tra quanti minuti rieseguire l'analisi per capire se è il momento di entrare in posizione, e i livelli di TP/SL.",
            "schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["buy", "sell", "wait"]
                    },
                    "next_check_minutes": {
                        "type": "integer"
                    },
                    "reason": {
                        "type": "string"
                    },
                    "take_profit_pct": {
                        "type": "number",
                        "description": "Percentuale suggerita per TP (es. 1.5 = 1.5%)"
                    },
                    "stop_loss_pct": {
                        "type": "number",
                        "description": "Percentuale suggerita per SL (es. 0.8 = 0.8%)"
                    }
                },
                "required": ["action", "next_check_minutes", "reason", "take_profit_pct", "stop_loss_pct"],
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
