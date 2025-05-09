def get_base_from_aritable(api: Api, base_name: str) -> Base:
    return list(filter(lambda item: item.name == base_name, api.bases()))[0]


def get_table_from_base(base: Base, table_name: str) -> Table:
    return list(filter(lambda item: item.name == table_name, base.tables()))[0]
