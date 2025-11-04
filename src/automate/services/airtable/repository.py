"""Airtable 저장소"""

import asyncio
from typing import Dict

from pyairtable import Api

from ...core.config import get_settings
from .client import get_base_from_aritable, get_table_from_base


async def save_to_airtable(video_id: str, record: Dict) -> None:
    """요약된 내용을 Airtable에 저장합니다."""
    settings = get_settings()

    api_key = settings.AIRTABLE_API_KEY
    if api_key is None:
        raise ValueError("AIRTABLE_API_KEY is not set")

    base_name = settings.AIRTABLE_BASE_NAME
    if base_name is None:
        raise ValueError("AIRTABLE_BASE_NAME is not set")

    table_name = settings.AIRTABLE_TABLE_NAME
    if table_name is None:
        raise ValueError("AIRTABLE_TABLE_NAME is not set")

    print("api_key", api_key)
    print("base_name", base_name)
    print("table_name", table_name)

    api = Api(api_key)
    base = await asyncio.to_thread(get_base_from_aritable, api, base_name)
    table = await asyncio.to_thread(get_table_from_base, base, table_name)
    await asyncio.to_thread(table.create, record)
