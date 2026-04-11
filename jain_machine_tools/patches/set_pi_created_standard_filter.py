import frappe


def execute():
    """Enable in_standard_filter on custom_pi_created field in Sales Order."""
    cf = frappe.db.get_value(
        "Custom Field",
        {"dt": "Sales Order", "fieldname": "custom_pi_created"},
        "name",
    )
    if cf:
        frappe.db.set_value("Custom Field", cf, "in_standard_filter", 1)
        frappe.db.commit()
