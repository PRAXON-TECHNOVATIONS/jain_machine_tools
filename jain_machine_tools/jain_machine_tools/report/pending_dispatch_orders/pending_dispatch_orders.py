# Copyright (c) 2026, Praxon Technovation and contributors
# For license information, please see license.txt

# import frappe


# def execute(filters=None):
# 	columns, data = [], []
# 	return columns, data

import frappe
from frappe.utils import flt, getdate, today


def execute(filters=None):
    filters = filters or {}

    columns = get_columns()
    data = get_data(filters)
    summary = get_summary(data)

    return columns, data, None, None, summary


def get_columns():
    return [
        {"label": "Sales Order", "fieldname": "sales_order", "fieldtype": "Data", "width": 200},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 140},
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": "Ordered Qty", "fieldname": "qty", "fieldtype": "Float", "width": 110},
        {"label": "Delivered Qty", "fieldname": "delivered_qty", "fieldtype": "Float", "width": 120},
        {"label": "Pending Qty", "fieldname": "pending_qty", "fieldtype": "Float", "width": 110},
        {"label": "Delivery %", "fieldname": "delivery_percent", "fieldtype": "Percent", "width": 100},
        {"label": "Delivery Date", "fieldname": "delivery_date", "fieldtype": "Date", "width": 120},
        {"label": "Dispatch Status", "fieldname": "dispatch_status", "fieldtype": "Data", "width": 160},
        {"label": "Overdue", "fieldname": "overdue", "fieldtype": "Data", "width": 90},
        {"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 140},
    ]


def get_conditions(filters):
    conditions = []

    if filters.get("company"):
        conditions.append("so.company = %(company)s")
    if filters.get("customer"):
        conditions.append("so.customer = %(customer)s")
    if filters.get("sales_order"):
        conditions.append("so.name = %(sales_order)s")
    if filters.get("warehouse"):
        conditions.append("soi.warehouse = %(warehouse)s")
    if filters.get("from_delivery_date"):
        conditions.append("so.delivery_date >= %(from_delivery_date)s")
    if filters.get("to_delivery_date"):
        conditions.append("so.delivery_date <= %(to_delivery_date)s")

    if filters.get("dispatch_status"):
        if filters.get("dispatch_status") == "Not Dispatched":
            conditions.append("soi.delivered_qty = 0")
        else:
            conditions.append("soi.delivered_qty > 0")

    return " AND ".join(conditions)


def get_data(filters):
    conditions = get_conditions(filters)

    query = f"""
        SELECT
            so.name AS sales_order,
            so.customer,
            so.delivery_date,
            soi.item_code,
            soi.qty,
            soi.delivered_qty,
            (soi.qty - soi.delivered_qty) AS pending_qty,
            soi.warehouse
        FROM `tabSales Order` so
        JOIN `tabSales Order Item` soi ON soi.parent = so.name
        WHERE
            so.docstatus = 1
            AND so.delivery_status IN ("Not Delivered", "Partly Delivered")
            AND (soi.qty - soi.delivered_qty) > 0
            {f"AND {conditions}" if conditions else ""}
        ORDER BY so.name, so.delivery_date
    """

    rows = frappe.db.sql(query, filters, as_dict=True)

    today_date = getdate(today())
    grouped = {}

    for r in rows:
        grouped.setdefault(r.sales_order, []).append(r)

    data = []

    for so, items in grouped.items():
        total_qty = sum(flt(i.qty) for i in items)
        total_delivered = sum(flt(i.delivered_qty) for i in items)
        total_pending = sum(flt(i.pending_qty) for i in items)

        delivery_percent = round((total_delivered / total_qty) * 100, 2) if total_qty else 0
        overdue = any(i.delivery_date and getdate(i.delivery_date) < today_date for i in items)

        # 🔹 Parent row
        data.append({
            "sales_order": so,
            "customer": items[0].customer,
            "qty": total_qty,
            "delivered_qty": total_delivered,
            "delivery_percent": delivery_percent,
            "pending_qty": total_pending,
            "delivery_date": items[0].delivery_date,
            "dispatch_status": "Not Dispatched" if delivery_percent == 0 else "Partially Dispatched",
            "overdue": "Yes" if overdue else "No",
            "indent": 0
        })

        # 🔹 Child rows
        for i in items:
            percent = round((flt(i.delivered_qty) / flt(i.qty)) * 100, 2) if i.qty else 0

            data.append({
                "sales_order": so,
                "item_code": i.item_code,
                "qty": i.qty,
                "delivered_qty": i.delivered_qty,
                "delivery_percent": percent,
                "pending_qty": i.pending_qty,
                "delivery_date": i.delivery_date,
                "dispatch_status": "Not Dispatched" if percent == 0 else "Partially Dispatched",
                "overdue": "Yes" if i.delivery_date and getdate(i.delivery_date) < today_date else "No",
                "warehouse": i.warehouse,
                "indent": 1
            })

    if filters.get("overdue_only"):
        data = [d for d in data if d.get("overdue") == "Yes"]

    return data


def get_summary(data):
    parents = [d for d in data if d.get("indent") == 0]

    return [
        {"label": "Pending Orders", "value": len(parents), "indicator": "Red"},
        {
            "label": "Partially Dispatched Orders",
            "value": sum(1 for d in parents if d["delivery_percent"] > 0),
            "indicator": "Orange",
        },
        {
            "label": "Overdue Orders",
            "value": sum(1 for d in parents if d["overdue"] == "Yes"),
            "indicator": "Red",
        },
    ]