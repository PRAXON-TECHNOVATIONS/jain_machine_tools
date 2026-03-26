import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	"""
	Ensure Sales Invoice has the delivery_date field used by Delivery Planning Schedule validation.
	Some sites received the legacy planning schedule field without the companion delivery date field.
	"""
	custom_fields = {
		"Sales Invoice": [
			{
				"fieldname": "delivery_date",
				"label": "Delivery Date",
				"fieldtype": "Date",
				"insert_after": "delivery_planning_schedule",
				"reqd": 0,
				"allow_on_submit": 0,
				"description": "Optional. Select a Delivery Date to invoice that specific plan only.",
			}
		]
	}

	create_custom_fields(custom_fields, update=True)
	frappe.db.commit()
