import frappe


def execute():
    """
    Add custom_pi_created (Check, read-only) to Sales Order.
    Shown in list view as "PI Created" — gets set when SO is made from Proforma Invoice.
    """
    if frappe.db.exists("Custom Field", {"dt": "Sales Order", "fieldname": "custom_pi_created"}):
        return

    frappe.get_doc(
        {
            "doctype": "Custom Field",
            "dt": "Sales Order",
            "fieldname": "custom_pi_created",
            "label": "PI Created",
            "fieldtype": "Check",
            "insert_after": "status",
            "read_only": 1,
            "in_standard_filter": 1,
            "default": "0",
        }
    ).insert(ignore_permissions=True)

    frappe.db.commit()
