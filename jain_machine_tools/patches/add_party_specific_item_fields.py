import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """
    Add custom fields to Party Specific Item doctype:
    1. Supplier Item Code - text field (visible when party_type == "Supplier" and party has value)
    """

    custom_fields = {
        "Party Specific Item": [
            # Supplier Item Code - shown when party_type is Supplier and party is selected
            {
                "fieldname": "supplier_item_code",
                "label": "Supplier Item Code",
                "fieldtype": "Data",
                "insert_after": "party",
                "depends_on": "eval:doc.party_type == 'Supplier' && doc.party",
                "description": "Item code used by the supplier for this item",
                "unique": 1,
            }
        ]
    }

    create_custom_fields(custom_fields, update=True)
    frappe.db.commit()

    print("Successfully added custom fields to Party Specific Item doctype")
