from datetime import datetime, timedelta
import os
from azure.data.tables import TableServiceClient, UpdateMode


connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
table_name = "CryptoStatus"
service = TableServiceClient.from_connection_string(connection_string)
table_client = service.get_table_client(table_name)

def get_crypto_status(symbol: str):
    try:
        return table_client.get_entity(partition_key=symbol, row_key="status")
    except:
        return None

def update_crypto_status(symbol: str, action: str, next_check_minutes: int, reason: str,
                         take_profit_pct: float = None, stop_loss_pct: float = None,
                         token_usage: int = None):
    entity = {
        "PartitionKey": symbol,
        "RowKey": "status",
        "action": action,
        "reason": reason,
        "next_check_time": (datetime.utcnow() + timedelta(minutes=next_check_minutes)).isoformat(),
        "timestamp": datetime.utcnow().isoformat()
    }

    if take_profit_pct is not None:
        entity["tp_pct"] = float(take_profit_pct)
    if stop_loss_pct is not None:
        entity["sl_pct"] = float(stop_loss_pct)
    if token_usage is not None:
        entity["tokens_total"] = token_usage

    table_client.upsert_entity(mode=UpdateMode.MERGE, entity=entity)