"""
Seed data for Motor Parameter Master
Run this script to populate the 10 standard parameters
"""

import frappe


def create_motor_parameters():
	"""Create 10 standard motor parameters"""

	parameters = [
		{
			"parameter_name": "VoltFr",
			"parameter_code": "VF",
			"description": "Voltage and Frequency customization",
			"applicable_to_flp": 1,
			"applicable_to_non_flp": 1,
			"frame_size_dependent": 1,
			"applies_to_all_frame_sizes": 0,
			"applicable_frame_sizes": "63,71,80,90,100,112,132,160,180,200,225,250,280,315,355",
			"pricing_type": "Percentage",
			"is_active": 1
		},
		{
			"parameter_name": "VPI",
			"parameter_code": "VPI",
			"description": "Vacuum Pressure Impregnation",
			"applicable_to_flp": 1,
			"applicable_to_non_flp": 1,
			"frame_size_dependent": 0,
			"applies_to_all_frame_sizes": 1,
			"pricing_type": "Percentage",
			"is_active": 1
		},
		{
			"parameter_name": "Space Heater",
			"parameter_code": "SH",
			"description": "Anti-condensation heater",
			"applicable_to_flp": 1,
			"applicable_to_non_flp": 1,
			"frame_size_dependent": 0,
			"applies_to_all_frame_sizes": 1,
			"pricing_type": "Fixed Amount",
			"is_active": 1
		},
		{
			"parameter_name": "Thermistor",
			"parameter_code": "TH",
			"description": "Temperature sensing device",
			"applicable_to_flp": 1,
			"applicable_to_non_flp": 1,
			"frame_size_dependent": 0,
			"applies_to_all_frame_sizes": 1,
			"pricing_type": "Fixed Amount",
			"is_active": 1
		},
		{
			"parameter_name": "IP Rating",
			"parameter_code": "IP",
			"description": "Ingress Protection rating change",
			"applicable_to_flp": 1,
			"applicable_to_non_flp": 1,
			"frame_size_dependent": 1,
			"applies_to_all_frame_sizes": 0,
			"applicable_frame_sizes": "63,71,80,90,100,112,132,160,180,200,225,250,280,315,355",
			"pricing_type": "Percentage",
			"is_active": 1
		},
		{
			"parameter_name": "Roller Bearing",
			"parameter_code": "RB",
			"description": "Roller bearing instead of ball bearing",
			"applicable_to_flp": 1,
			"applicable_to_non_flp": 1,
			"frame_size_dependent": 1,
			"applies_to_all_frame_sizes": 0,
			"applicable_frame_sizes": "160,180,200,225,250,280,315,355",
			"pricing_type": "Percentage",
			"is_active": 1
		},
		{
			"parameter_name": "Insulated Bearing",
			"parameter_code": "IB",
			"description": "Insulated bearing for VFD applications",
			"applicable_to_flp": 0,
			"applicable_to_non_flp": 1,
			"frame_size_dependent": 0,
			"applies_to_all_frame_sizes": 1,
			"pricing_type": "Fixed Amount",
			"is_active": 1
		},
		{
			"parameter_name": "Class H",
			"parameter_code": "CH",
			"description": "Class H insulation",
			"applicable_to_flp": 1,
			"applicable_to_non_flp": 1,
			"frame_size_dependent": 0,
			"applies_to_all_frame_sizes": 1,
			"pricing_type": "Percentage",
			"is_active": 1
		},
		{
			"parameter_name": "Forced Cooling",
			"parameter_code": "FC",
			"description": "Forced air cooling system",
			"applicable_to_flp": 0,
			"applicable_to_non_flp": 1,
			"frame_size_dependent": 1,
			"applies_to_all_frame_sizes": 0,
			"applicable_frame_sizes": "132,160,180,200,225,250,280,315,355",
			"pricing_type": "Fixed Amount",
			"is_active": 1
		},
		{
			"parameter_name": "ATEX Certification",
			"parameter_code": "ATEX",
			"description": "ATEX certification for explosive atmospheres",
			"applicable_to_flp": 1,
			"applicable_to_non_flp": 0,
			"frame_size_dependent": 0,
			"applies_to_all_frame_sizes": 1,
			"pricing_type": "Percentage",
			"is_active": 1
		}
	]

	created = 0
	skipped = 0

	for param_data in parameters:
		# Check if parameter already exists
		if frappe.db.exists("Motor Parameter Master", param_data["parameter_name"]):
			print(f"Parameter '{param_data['parameter_name']}' already exists, skipping...")
			skipped += 1
			continue

		# Create new parameter
		param = frappe.get_doc({
			"doctype": "Motor Parameter Master",
			**param_data
		})
		param.insert()
		created += 1
		print(f"Created parameter: {param_data['parameter_name']}")

	frappe.db.commit()

	print(f"\nSummary: {created} created, {skipped} skipped")
	return {"created": created, "skipped": skipped}


if __name__ == "__main__":
	# For direct execution via bench execute
	create_motor_parameters()
