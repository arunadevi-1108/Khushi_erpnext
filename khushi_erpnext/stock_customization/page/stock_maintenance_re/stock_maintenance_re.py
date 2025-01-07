import frappe


def build_where_clause(filters: dict) -> str:
    """
    Constructs a SQL Where clause string based on the provided filters.
    Args:
        filters (dict):  containing filter keys and values for filtering the items.
    Returns:
        str: A SQL condition string that adds filters to the WHERE clause.
    """

    condition: str = ""
    if filters.get('item_group'):
        condition += f"AND smr.item_group = '{filters.get('item_group')}' "

    if filters.get('brand'):
        condition += f"AND smr.brand = '{filters.get('brand')}' "

    if filters.get('year'):
        condition += f"AND smr.custom_year = '{filters.get('year')}' "

    if filters.get('subject'):
        condition += f"AND smr.custom_subject = '{filters.get('subject')}' "

    if filters.get('status'):
        condition += f"AND smr.custom_status = '{filters.get('status')}' "

    if filters.get('season'):
        condition += f"AND smr.custom_item_season = '{filters.get('season')}' "

    if filters.get('item'):
        condition += f"AND smr.item = '{filters.get('item')}' "

    if filters.get('warehouse'):
        condition += f"AND smr.warehouse = '{filters.get('warehouse')}' "

    where_clause: str = f"WHERE smr.disabled = 0 AND smr.is_stock_item = 1 {condition}"

    return where_clause


def build_having_clause(filters: dict) -> str:
    """
    Constructs a SQL Having clause string based on the provided filters.
    Args:
        filters (dict): containing filter keys and values for filtering the items.
    Returns:
        str: A SQL condition string that adds filters to the Having clause.
    """
    comparison_type: str | None = filters.get('comparison_type', None)
    qty: int = filters.get('qty', 0)
    having: str = ""
    qty_field: str = "smr.total_qty " if filters.get('warehouse', None) else "SUM(smr.total_qty)"

    if comparison_type:
        if comparison_type == 'Between':
            having += f"""HAVING {qty_field} BETWEEN {filters.get("qty_from", 0)} AND {filters.get("qty_to", 0)} """

        elif comparison_type == 'Less than or Equal to':
            having += f"HAVING {qty_field} <= {qty} "

        elif comparison_type == 'Less than':
            having += f"HAVING {qty_field} < {qty} "

        elif comparison_type == 'Greater than or Equal to':
            having += f"HAVING {qty_field} >= {qty} "

        elif comparison_type == 'Greater than':
            having += f"HAVING {qty_field} > {qty} "

        elif comparison_type == 'Not Equals':
            having += f"HAVING {qty_field} != {qty} "

        elif comparison_type == 'Equals':
            having += f"HAVING {qty_field} = {qty} "

    return having


def build_group_by_clause(filters: dict) -> str:
    """
    Constructs a SQL Group By clause string based on the provided filters.
    Args:
        filters (dict): Dicsionary containing filter keys and values for filtering the items.
    Returns:
        str: A SQL condition string that adds filters to the Group By clause.
    """

    group_by: str = "" if filters.get('warehouse', None) else "GROUP BY smr.item"
    return group_by


def build_limit_clause(filters: dict) -> str:
    page_size: str | int = filters.get('page_limit')
    if page_size == "All":
        return ""
    else:
        return f"LIMIT {page_size} "


def get_query(filters: dict) -> str:
    """
    Constructs a SQL Query string based on the provided filters.
    Args:
        filters (dict): Dicsionary containing filter keys and values for filtering the items.
    Returns:
        str: Query
    """
    qty_field: str = "smr.total_qty AS qty" if filters.get('warehouse', None) else "SUM(smr.total_qty) AS qty"
    where: str = build_where_clause(filters)
    group_by: str = build_group_by_clause(filters)
    having: str = build_having_clause(filters)
    limit: str = build_limit_clause(filters)
    content_query: str = f"""
                SELECT 
                    smr.item AS item,
                    smr.item_group AS item_group,
                    smr.brand AS brand,
                    smr.image AS image,
                    {qty_field}
                FROM 
                    stock_maintains_report_view smr 
                {where}
                {group_by}
                {having}
                {limit}
             """

    total_count_query: str = f""" SELECT {qty_field} FROM stock_maintains_report_view smr {where} {group_by} {having} """
    return content_query, total_count_query


@frappe.whitelist()
def get_data(filters: str) -> tuple:
    """
    Retrieves item data based on specified filters.
    Args:
        filters (str): JSON string containing filter criteria for retrieving item data.
    Returns:
        list[dict] | None: A list of item dict that match the filter criteria or None if no data.
    """
    filters: dict = frappe.parse_json(filters)
    content_query, total_count_query = get_query(filters)
    data: list[dict] = frappe.db.sql(content_query, as_dict=True)
    total_count: list = frappe.db.sql(total_count_query,pluck='qty')
    return data, len(total_count), sum(total_count) if total_count else 0
