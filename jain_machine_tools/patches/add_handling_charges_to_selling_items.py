import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    
	"""
	Add handling charges custom fields to all selling item doctypes:
	- Quotation Item
	- Sales Order Item
	- Sales Invoice Item
	- Delivery Note Item

	Fields added:
	1. handling_charges_section - Section Break
	2. handling_charges_type - Select (Percentage/Amount)
	3. handling_charges_percentage - Percent field
	4. handling_charges_amount - Currency field
	5. handling_charges_value - Currency field
	"""
	# Define item doctypes
	item_doctypes = [
		"Quotation Item",
		"Sales Order Item",
		"Sales Invoice Item",
		"Delivery Note Item"
	]

	custom_fields = {}

	# Create fields for each doctype
	for doctype in item_doctypes:
		custom_fields[doctype] = [
			# Section Break
			{
				"fieldname": "handling_charges_section",
				"label": "Handling Charges",
				"fieldtype": "Section Break",
				"insert_after": "discount_and_margin",
				"collapsible": 1,
				"collapsible_depends_on": "eval: doc.handling_charges_type"
			},

			# Handling Charges Type
			{
				"fieldname": "handling_charges_type",
				"label": "Handling Charges Type",
				"fieldtype": "Select",
				"options": "\nPercentage\nAmount",
				"insert_after": "handling_charges_section",
				"description": "Select whether handling charges are calculated as a percentage of rate or as a fixed amount",
				"print_hide": 1
			},

			# Handling Charges Percentage
			{
				"fieldname": "handling_charges_percentage",
				"label": "Handling Charges (%)",
				"fieldtype": "Percent",
				"insert_after": "handling_charges_type",
				"depends_on": "eval: doc.handling_charges_type == 'Percentage'",
				"non_negative": 1,
				"print_hide": 1
			},

			# Handling Charges Amount
			{
				"fieldname": "handling_charges_amount",
				"label": "Handling Charges Amount",
				"fieldtype": "Currency",
				"options": "currency",
				"insert_after": "handling_charges_percentage",
				"depends_on": "eval: doc.handling_charges_type == 'Amount'",
				"non_negative": 1,
				"print_hide": 1
			},

			# Base Rate Before Handling Charges (Hidden field to store base rate)
			{
				"fieldname": "base_rate_before_handling_charges",
				"label": "Base Rate Before Handling Charges",
				"fieldtype": "Currency",
				"options": "currency",
				"insert_after": "handling_charges_amount",
				"hidden": 1,
				"print_hide": 1,
				"read_only": 1,
				"no_copy": 1
			},
   
			# Handling Charges Value (Total, for Print)
			{
                "fieldname": "handling_charges_value",
                "label": "Handling Charges",
                "fieldtype": "Currency",
                "options": "currency",
                "insert_after": "base_rate_before_handling_charges",
                "read_only": 1,
                "print_hide": 0,
                "no_copy": 1
            }
		]

	# Create the custom fields
	create_custom_fields(custom_fields, update=True)
	frappe.db.commit()

	print("Successfully added handling charges fields to all selling item doctypes")
