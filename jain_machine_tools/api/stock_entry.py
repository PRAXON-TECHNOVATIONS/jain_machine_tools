import frappe


@frappe.whitelist()
def get_warehouse_names():
	"""
	Return active, non-group warehouse names for dropdown selection.
	Uses get_all so users without Warehouse read permission can still fetch names.
	"""
	return frappe.get_all(
		"Warehouse",
		filters={"disabled": 0, "is_group": 0},
		pluck="name",
		order_by="name asc",
	)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_warehouse_names_query(doctype, txt, searchfield, start, page_len, filters):
	"""
	Link-field query for warehouses.
	Returns names even when user does not have Warehouse master access.
	"""
	return frappe.db.sql(
		"""
		SELECT name
		FROM `tabWarehouse`
		WHERE disabled = 0
			AND is_group = 0
			AND name LIKE %(txt)s
		ORDER BY name ASC
		LIMIT %(start)s, %(page_len)s
		""",
		{
			"txt": f"%{txt}%",
			"start": start,
			"page_len": page_len,
		},
	)
