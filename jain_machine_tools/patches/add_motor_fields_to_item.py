"""
Add frame_size and is_flameproof custom fields to Item doctype
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """
    Add custom fields to Item for motor specifications:
    - frame_size: Select field for motor frame sizes
    - is_flameproof: Checkbox to indicate if motor is flameproof (FLP)

    These fields are used to filter applicable parameters in Supplier Motor Configuration
    """

    # Delete existing frame_size field if it exists with wrong type
    existing_field = frappe.db.exists("Custom Field", {"dt": "Item", "fieldname": "frame_size"})
    if existing_field:
        try:
            frappe.delete_doc("Custom Field", existing_field, force=True)
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Error deleting frame_size custom field: {e}")

    custom_fields = {
        "Item": [
            {
                "fieldname": "frame_size",
                "label": "Frame Size",
                "fieldtype": "Data",
                "insert_after": "stock_uom",
                "description": "Motor frame size - determines applicable parameters (e.g., 63, 71, 80, 90, etc.)"
            },
            {
                "fieldname": "is_flameproof",
                "label": "Is Flameproof (FLP)",
                "fieldtype": "Check",
                "insert_after": "frame_size",
                "default": "0",
                "description": "Check if this is a flameproof motor - determines applicable parameters"
            },
        ]
    }

    create_custom_fields(custom_fields, update=True)
    frappe.db.commit()

