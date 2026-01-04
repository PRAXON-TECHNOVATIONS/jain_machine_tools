"""
Script to update existing motor parameters with categories for tab-based UI
Run via: bench execute jain_machine_tools.jain_machine_tools.fixtures.update_parameter_categories.update_categories
"""

import frappe


def update_categories():
	"""Update existing motor parameters with appropriate categories"""

	# Define category mapping
	category_mapping = {
		"VoltFr": "Electrical",
		"VPI": "Insulation",
		"Space Heater": "Electrical",
		"Thermistor": "Electrical",
		"IP Rating": "Mechanical",
		"Roller Bearing": "Mechanical",
		"Insulated Bearing": "Mechanical",
		"Class H": "Insulation",
		"Forced Cooling": "Cooling",
		"ATEX Certification": "Certification"
	}

	updated = 0
	not_found = []

	for param_name, category in category_mapping.items():
		if frappe.db.exists("Motor Parameter Master", param_name):
			frappe.db.set_value("Motor Parameter Master", param_name, "category", category)
			print(f"✓ Updated {param_name} → {category}")
			updated += 1
		else:
			print(f"✗ Parameter '{param_name}' not found")
			not_found.append(param_name)

	frappe.db.commit()

	print(f"\n{'='*50}")
	print(f"Summary: {updated} parameters updated")
	if not_found:
		print(f"Not found: {', '.join(not_found)}")
	print(f"{'='*50}\n")

	return {"updated": updated, "not_found": not_found}


if __name__ == "__main__":
	update_categories()
