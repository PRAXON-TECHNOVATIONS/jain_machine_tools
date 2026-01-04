import frappe

@frappe.whitelist()
def cancel_with_reason(docname, reason):
    frappe.db.set_value(
        "Request for Quotation",
        docname,
        "custom_cancel_reason",
        reason,
        update_modified=False
    )
    doc = frappe.get_doc("Request for Quotation", docname)
    doc.cancel()
def before_insert(doc, method):
    doc.custom_cancel_reason = None



