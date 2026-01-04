import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """
    Add custom fields to Item doctype:
    1. Is Standard - checkbox (visible only when item_group == "Electric Motor")
    2. Warranty section with fields (visible when has_serial_no is checked)
    """

    custom_fields = {
        "Item": [
            # Is Standard checkbox - visibility controlled by client script (item.js)
            # Shows when parent_item_group == "Electric Motor"
            {
                "fieldname": "is_non_standard",
                "label": "Is Non Standard",
                "fieldtype": "Check",
                "insert_after": "item_group",
                "description": "Check if this is a non standard item"
            },

            # Warranty Section - shown when has_serial_no is checked
            {
                "fieldname": "warranty_section",
                "label": "Warranty Details",
                "fieldtype": "Section Break",
                "insert_after": "serial_no_series",
                "depends_on": "eval:doc.has_serial_no == 1",
                "collapsible": 0
            },

            # Warranty UOM - Days/Months/Years
            {
                "fieldname": "warranty_uom",
                "label": "Warranty UOM",
                "fieldtype": "Select",
                "options": "Days\nMonths\nYears",
                "insert_after": "warranty_section",
                "mandatory_depends_on": "eval:doc.has_serial_no == 1",
                "depends_on": "eval:doc.has_serial_no == 1"
            },

            # Warranty Start From - Delivery Note or Sales Invoice posting date
            {
                "fieldname": "warranty_start_from",
                "label": "Warranty Start From",
                "fieldtype": "Select",
                "options": "Delivery Note Posting Date\nSales Invoice Posting Date",
                "insert_after": "warranty_uom",
                "mandatory_depends_on": "eval:doc.has_serial_no == 1",
                "depends_on": "eval:doc.has_serial_no == 1"
            },

            # Column Break
            {
                "fieldname": "warranty_column_break",
                "fieldtype": "Column Break",
                "insert_after": "warranty_start_from",
                "depends_on": "eval:doc.has_serial_no == 1"
            },

            # Warranty Period - integer field
            {
                "fieldname": "company_warranty_period",
                "label": "Warranty Period",
                "fieldtype": "Int",
                "insert_after": "warranty_column_break",
                "mandatory_depends_on": "eval:doc.has_serial_no == 1",
                "depends_on": "eval:doc.has_serial_no == 1",
                "description": "Number of warranty periods (e.g., 12 for 12 months)"
            }
        ]
    }

    create_custom_fields(custom_fields, update=True)
    frappe.db.commit()

    print("Successfully added custom fields to Item doctype")
