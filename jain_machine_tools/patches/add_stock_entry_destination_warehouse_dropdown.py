import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	"""
	Add Destination Warehouse dropdown on Stock Entry for Material Transfer.
	"""
	custom_fields = {
		"Stock Entry": [
			{
				"fieldname": "destination_warehouse_select",
				"label": "Destination Warehouse",
				"fieldtype": "Link",
				"options": "Warehouse",
				"insert_after": "to_warehouse",
				"depends_on": "eval:doc.purpose == 'Material Transfer'",
				"mandatory_depends_on": "eval:doc.purpose == 'Material Transfer'",
				"description": "Select destination warehouse for material transfer",
			}
		]
	}

	create_custom_fields(custom_fields, update=True)
	frappe.db.commit()
