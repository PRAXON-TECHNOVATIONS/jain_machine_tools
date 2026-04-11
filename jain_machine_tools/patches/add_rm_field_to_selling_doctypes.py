import frappe


def execute():
    """Add custom_rm (RM) Link field to Sales Order and Quotation doctypes."""
    for dt in ("Sales Order", "Quotation"):
        if frappe.db.exists("Custom Field", {"dt": dt, "fieldname": "custom_rm"}):
            continue

        frappe.get_doc(
            {
                "doctype": "Custom Field",
                "dt": dt,
                "fieldname": "custom_rm",
                "label": "RM",
                "fieldtype": "Link",
                "options": "Employee",
                "insert_after": "customer_group",
            }
        ).insert(ignore_permissions=True)

    frappe.db.commit()
