import frappe

def validate_duplicate_sq(doc, method):
    # Supplier must exist
    if not doc.supplier:
        return

    # RFQ is NOT on parent — it's inside items table
    rfq = None
    for item in doc.items:
        if item.request_for_quotation:
            rfq = item.request_for_quotation
            break

    if not rfq:
        return  # no RFQ → no duplicate check

    # Check if another SQ exists for same Supplier + RFQ
    existing = frappe.db.sql("""
        SELECT sq.name
        FROM `tabSupplier Quotation` sq
        JOIN `tabSupplier Quotation Item` sqi ON sqi.parent = sq.name
        WHERE sq.supplier = %s
          AND sqi.request_for_quotation = %s
          AND sq.docstatus < 2
          AND sq.name != %s
        LIMIT 1
    """, (doc.supplier, rfq, doc.name), as_dict=True)

    if existing:
        frappe.throw(
            f"Supplier quotation for this Supplier & RFQ already exists.<br><br>"
            f"Existing SQTN: <b>{existing[0].name}</b>"
        )
