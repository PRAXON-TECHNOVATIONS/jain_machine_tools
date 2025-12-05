import frappe

@frappe.whitelist()
def cancel_with_reason(docname, reason):
    doc = frappe.get_doc("Request for Quotation", docname)
    
    # Set cancel reason before cancelling
    doc.db_set("custom_cancel_reason", reason)  # db_set bypasses cannot-update-after-submit issue
    
    # Cancel the document
    doc.cancel()
    
    return "Cancelled"
