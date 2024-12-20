import frappe


def create_soiq_view():
    query = """
           CREATE OR REPLACE
            ALGORITHM = UNDEFINED VIEW `veuSales Order Item Quantity` AS
            SELECT so.transaction_date, so.name, so.status, so.customer, soi.item_code, soi.qty, so.company FROM `tabSales Order` AS so
            JOIN `tabSales Order Item` AS soi ON so.name = soi.parent;
            """
    frappe.db.sql(query)
    frappe.db.commit()
    print("----------------- View Created for Sales Order Item Quantity ------------------------ ")


def create_poiq_view():
    query = """
           CREATE OR REPLACE
            ALGORITHM = UNDEFINED VIEW `veuPurchase Order Item Quantity` AS 
            SELECT COALESCE(poi.qty, 0) - COALESCE(poi.received_qty, 0) AS "poi_qty",
                  poi.item_code AS "item_code", po.supplier AS supplier
            FROM `tabPurchase Order` AS po
                 JOIN `tabPurchase Order Item` AS poi ON po.name = poi.parent
            WHERE po.status NOT IN ("To Bill", "Completed", "Cancelled", "Closed", "Delivered") HAVING poi_qty > 0;
            """
    frappe.db.sql(query)
    frappe.db.commit()
    print("----------------- View Created for Purchase Order Item Quantity ------------------------ ")


def create_scirq_view():
    query = """
           CREATE OR REPLACE
            ALGORITHM = UNDEFINED VIEW `veuSubcontracting Item Quantity` AS
            SELECT COALESCE(scoi.qty, 0) - COALESCE(scoi.received_qty, 0) as "subcontract_qty", scoi.item_code, sco.supplier as jobber
            FROM `tabSubcontracting Order` AS sco
                     JOIN `tabSubcontracting Order Item` AS scoi ON sco.name = scoi.parent
            WHERE sco.status NOT IN ("Completed", "Cancelled", "Closed") HAVING subcontract_qty > 0;
            """
    frappe.db.sql(query)
    frappe.db.commit()
    print("----------------- View Created for Subcontracting Item Receive Quantity ------------------------ ")


def execute():
    create_soiq_view()
    create_poiq_view()
    create_scirq_view()
