import frappe

@frappe.whitelist()
def save_pr(name):
    """
    Save Purchase Receipt from popup close
    """
    doc = frappe.get_doc("Purchase Receipt", name)

    if doc.docstatus != 0:
        return

    doc.save(ignore_permissions=True)
