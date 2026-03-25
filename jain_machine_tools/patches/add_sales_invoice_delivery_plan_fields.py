import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	"""
	Add the Delivery Plan selection table on Sales Invoice and hide legacy single-value fields.
	"""
	custom_fields = {
		"Sales Invoice": [
			{
				"fieldname": "delivery_plan_section",
				"label": "Delivery Plans",
				"fieldtype": "Section Break",
				"insert_after": "connections_tab",
			},
			{
				"fieldname": "delivery_plan_details",
				"label": "Selected Delivery Plans",
				"fieldtype": "Table",
				"options": "Sales Invoice Delivery Plan",
				"insert_after": "delivery_plan_section",
				"description": "Optional. Use this only when the invoice should be linked with Delivery Planning Schedule rows.",
			},
		]
	}

	create_custom_fields(custom_fields, update=True)

	for fieldname in ("delivery_planning_schedule", "delivery_date"):
		if frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": fieldname}):
			frappe.db.set_value("Custom Field", {"dt": "Sales Invoice", "fieldname": fieldname}, "hidden", 1)
			frappe.db.set_value("Custom Field", {"dt": "Sales Invoice", "fieldname": fieldname}, "reqd", 0)

	frappe.clear_cache(doctype="Sales Invoice")
	frappe.db.commit()
