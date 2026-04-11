import frappe


def execute():
    """
    Add billing_status and delivery_status to Sales Order list view
    using Property Setters (Frappe best practice for overriding core doctype field properties).
    """
    for fieldname in ("billing_status", "delivery_status"):
        existing = frappe.db.exists(
            "Property Setter",
            {
                "doc_type": "Sales Order",
                "field_name": fieldname,
                "property": "in_list_view",
            },
        )
        if existing:
            frappe.db.set_value("Property Setter", existing, "value", "1")
        else:
            frappe.get_doc(
                {
                    "doctype": "Property Setter",
                    "doc_type": "Sales Order",
                    "field_name": fieldname,
                    "property": "in_list_view",
                    "property_type": "Check",
                    "value": "1",
                    "doctype_or_field": "DocField",
                }
            ).insert(ignore_permissions=True)

    frappe.db.commit()
