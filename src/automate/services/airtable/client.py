"""Airtable 클라이언트 관리"""

import asyncio
from pyairtable import Api, Base, Table

from ...core.config import get_settings


def get_base_from_aritable(api: Api, base_name: str) -> Base:
    """Airtable API에서 Base 객체를 가져옵니다."""
    return list(filter(lambda item: item.name == base_name, api.bases()))[0]


def get_table_from_base(base: Base, table_name: str) -> Table:
    """Base에서 Table 객체를 가져옵니다."""
    return list(filter(lambda item: item.name == table_name, base.tables()))[0]
