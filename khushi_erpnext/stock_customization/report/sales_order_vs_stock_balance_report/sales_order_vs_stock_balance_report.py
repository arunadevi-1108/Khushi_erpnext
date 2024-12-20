# Copyright (c) 2024, TechInsights and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.caching import redis_cache


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns() -> list[dict]:
    """Return the required Columns"""
    columns = [
        {"label": "Date", "fieldname": "date", "fieldtype": "Date"},
        {"label": "Sales Order", "fieldname": "sales_order", "fieldtype": "Link", "options": "Sales Order", "width": 220},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data"},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 180},
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 180},
        {"label": "Qty to Deliver", "fieldname": "qty_to_deliver", "fieldtype": "float"},
        {"label": "Stock Balance", "fieldname": "stock_balance", "fieldtype": "float"},
        {"label": "Purchase Qty Pending", "fieldname": "purchase_qty", "fieldtype": "float"},
        {"label": "Supplier", "fieldname": "supplier", "fieldtype": "Data", "width": 220},
        {"label": "Subcontract Qty Pending", "fieldname": "subcontract_qty", "fieldtype": "float"},
        {"label": "Jobber", "fieldname": "jobber", "fieldtype": "Data",  "width": 220},
        {"label": "Qty Needed", "fieldname": "qty_needed", "fieldtype": "float"}
    ]
    return columns


def get_select_field(filters: dict) -> str:
    """Return the select statement based on the filters"""
    select_fields = """so.transaction_date as "Date",so.name as "Sales Order",so.status as "Status",
    so.customer as "Customer", so.item_code as "Item Code",
    so.qty as "qty_to_deliver", COALESCE(b.actual_qty, 0) AS "stock_qty",
    COALESCE(poiq.poi_qty, 0) AS "poi_qty", poiq.supplier,
    COALESCE(scirq.subcontract_qty, 0) AS "subcontract_qty", scirq.jobber,
    so.qty - (COALESCE(b.actual_qty, 0) + COALESCE(poiq.poi_qty, 0) + COALESCE(scirq.subcontract_qty, 0)) AS qty_needed"""
    group_by_item: int = filters.get("group_by_item", 0)
    if group_by_item:
        select_fields = """GROUP_CONCAT(DISTINCT so.transaction_date) as "Date",
        GROUP_CONCAT(DISTINCT so.name) as "Sales Order", GROUP_CONCAT(DISTINCT so.status) as "Status",
        GROUP_CONCAT(DISTINCT so.customer) as "Customer", so.item_code as "Item Code", SUM(so.qty) as "qty_to_deliver",
        COALESCE(b.actual_qty, 0) AS "stock_qty", COALESCE(poiq.poi_qty, 0) AS "poi_qty", poiq.supplier,
        COALESCE(scirq.subcontract_qty, 0) AS "subcontract_qty", scirq.jobber, 
        SUM(so.qty) - (COALESCE(b.actual_qty, 0) + COALESCE(poiq.poi_qty, 0) + COALESCE(scirq.subcontract_qty, 0)) AS qty_needed"""
    return select_fields


def get_bin_query(warehouse: str = None) -> str:
    """Used to get the stock quantity"""
    cond: str = ""
    if warehouse:
        cond += f"WHERE warehouse = '{warehouse}'"
    bin_query: str = f"""SELECT SUM(actual_qty) AS actual_qty, item_code FROM `tabBin`
    {cond} GROUP BY item_code"""
    return bin_query


def get_poiq_query() -> str:
    """Used to get the purchase order quantity"""
    poiq_query: str = """SELECT sum(poiq.poi_qty) AS poi_qty, poiq.item_code,
     GROUP_CONCAT(DISTINCT poiq.supplier) AS supplier FROM
            `veuPurchase Order Item Quantity` AS poiq GROUP BY poiq.item_code"""
    return poiq_query


def get_scirq_query() -> str:
    """Used to get the Subcontrating order quantity to receive"""
    scirq_query: str = """SELECT SUM(scirq.subcontract_qty) AS subcontract_qty, scirq.item_code AS item_code, 
    GROUP_CONCAT(DISTINCT scirq.jobber) AS jobber  FROM
            `veuSubcontracting Item Quantity` AS scirq GROUP BY scirq.item_code"""
    return scirq_query


def get_join(filters: dict) -> str:
    """Return the join string"""
    bin_query: str = get_bin_query(filters.get("warehouse", None))
    poiq_query: str = get_poiq_query()
    scirq_query: str = get_scirq_query()
    join = f"""LEFT JOIN ({bin_query}) as b ON b.item_code = so.item_code
                LEFT JOIN ({poiq_query}) AS poiq ON poiq.item_code = so.item_code
                LEFT JOIN ({scirq_query}) AS scirq ON scirq.item_code = so.item_code"""
    return join


def get_condition(filters: dict) -> str:
    """Returns the where clause condition based on filters"""
    cond_list: list = ["so.status not in ('Completed', 'Cancelled', 'Closed')"]
    company: str = filters.get("company", "")
    f_date: "str" = filters.get("f_date", "")
    t_date: "str" = filters.get("t_date", "")
    sales_order: str = filters.get("sales_order", "")
    item_group: str = filters.get("item_group", "")
    status: tuple = tuple(filters.get("status", []))
    if company:
        cond_list.append(f"so.company = '{company}'")
    if f_date:
        cond_list.append(f"so.transaction_date >= '{f_date}'")
    if t_date:
        cond_list.append(f"so.transaction_date <= '{t_date}'")
    if sales_order:
        cond_list.append(f"so.name = '{sales_order}'")
    if item_group:
        cond_list.append(f"so.item_code in (SELECT item_name FROM tabItem WHERE item_group = '{item_group}')")
    if status:
        if len(status) == 1:
            cond_list.append(f"so.status = '{status[0]}'")
        else:
            cond_list.append(f"so.status IN {status}")
    cond: str = f"WHERE {' AND '.join(cond_list)}" if cond_list else ""
    return cond


def get_group_by(filters: dict) -> str:
    """Give the group by string"""
    group_by: str = ""
    group_by_item: int = filters.get("group_by_item", 0)
    if group_by_item:
        group_by += "GROUP BY so.item_code"
    return group_by

def get_having(filters: dict) -> str:
    cond_list=[]
    additional_qty_needed: int = filters.get("additional_qty_needed", 0)
    supplier: str = filters.get("supplier", "")
    jobber: str = filters.get("jobber", "")
    if additional_qty_needed:
        cond_list.append(f"qty_to_deliver > stock_qty + poi_qty + subcontract_qty")
    if supplier:
        cond_list.append(f"supplier LIKE '%{supplier}%'")
    if jobber:
        cond_list.append(f"jobber LIKE '%{jobber}%'")
    cond: str = f"HAVING {' AND '.join(cond_list)}" if cond_list else ""
    return cond

def form_sql_query(filters: dict) -> str:
    """Form the complete sql query"""
    select_fields: str = get_select_field(filters)
    join: str = get_join(filters)
    cond: str = get_condition(filters)
    group_by: str = get_group_by(filters)
    having: str = get_having(filters)
    query =f"""SELECT {select_fields} FROM `veuSales Order Item Quantity` AS so
                    {join} {cond} {group_by} {having}"""
    return query


def get_data(filters: dict) -> list[list]:
    """Give the data"""
    query: str = form_sql_query(filters)
    data = frappe.db.sql(query, as_list=True)
    return data

