# Copyright (c) 2026, Praxon Technovation and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "Stock Entry", "fieldname": "stock_entry", "fieldtype": "Link", "options": "Stock Entry", "width": 150},
		{"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 160},
		{"label": "Origin Date", "fieldname": "origin_date", "fieldtype": "Date", "width": 120},
		{"label": "Expected Delivery Date", "fieldname": "expected_delivery_date", "fieldtype": "Date", "width": 170},
		{"label": "Source Warehouse", "fieldname": "source_warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 220},
		{"label": "Destination Warehouse", "fieldname": "destination_warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 220},
		{"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 160},
		{"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 220},
		{"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 90},
		{"label": "UOM", "fieldname": "uom", "fieldtype": "Link", "options": "UOM", "width": 90},
		{"label": "In Transit", "fieldname": "add_to_transit", "fieldtype": "Check", "width": 100},
	]


def get_data(filters):
	conditions = ["se.purpose = 'Material Transfer'", "se.docstatus = 1"]
	params = {}

	if filters.get("source_warehouse"):
		conditions.append("sed.s_warehouse = %(source_warehouse)s")
		params["source_warehouse"] = filters.source_warehouse

	if filters.get("destination_warehouse"):
		conditions.append("sed.t_warehouse = %(destination_warehouse)s")
		params["destination_warehouse"] = filters.destination_warehouse

	return frappe.db.sql(
		f"""
		SELECT
			se.name AS stock_entry,
			se.company AS company,
			se.posting_date AS origin_date,
			se.posting_date AS expected_delivery_date,
			sed.s_warehouse AS source_warehouse,
			sed.t_warehouse AS destination_warehouse,
			sed.item_code AS item_code,
			sed.item_name AS item_name,
			sed.qty AS qty,
			sed.uom AS uom,
			se.add_to_transit AS add_to_transit
		FROM `tabStock Entry` se
		INNER JOIN `tabStock Entry Detail` sed ON sed.parent = se.name
		WHERE {" AND ".join(conditions)}
		ORDER BY se.posting_date DESC, se.name DESC, sed.idx ASC
		""",
		params,
		as_dict=True,
	)
