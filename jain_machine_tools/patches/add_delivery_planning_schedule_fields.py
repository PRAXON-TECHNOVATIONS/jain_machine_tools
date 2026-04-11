import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	"""
	Add mandatory Delivery Planning Schedule and Delivery Date fields on Sales Invoice.
	"""
	custom_fields = {
		"Sales Invoice": [
			{
				"fieldname": "delivery_planning_schedule",
				"label": "Delivery Planning Schedule",
				"fieldtype": "Link",
				"options": "Delivery Planning Schedule",
				"insert_after": "sales_order",
				"reqd": 0,
				"hidden": 1,
				"allow_on_submit": 0,
				"description": "Legacy field kept for compatibility.",
			},
			{
				"fieldname": "delivery_date",
				"label": "Delivery Date",
				"fieldtype": "Date",
				"insert_after": "delivery_planning_schedule",
				"reqd": 0,
				"allow_on_submit": 0,
				"description": "Invoice only the schedule rows planned for this delivery date.",
			}
		]
	}

	create_custom_fields(custom_fields, update=True)
	frappe.db.commit()
