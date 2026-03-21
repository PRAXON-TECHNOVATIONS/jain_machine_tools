import frappe


def execute():
	"""
	Convert destination_warehouse_select custom field from Select to Link(Warehouse)
	to avoid static Select option validation errors.
	"""
	custom_field_name = frappe.db.get_value(
		"Custom Field",
		{"dt": "Stock Entry", "fieldname": "destination_warehouse_select"},
		"name",
	)

	if not custom_field_name:
		return

	frappe.db.set_value(
		"Custom Field",
		custom_field_name,
		{
			"fieldtype": "Link",
			"options": "Warehouse",
		},
		update_modified=False,
	)
	frappe.clear_cache(doctype="Stock Entry")
