import frappe


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_stock_entry_repack(doctype, txt, searchfield, start, page_len, filters):
    """
    Get Stock Entry records where:
    1. purpose = 'Repack' (direct)
    2. OR stock_entry_type has purpose = 'Repack' (custom stock entry types)
    """

    return frappe.db.sql("""
        SELECT DISTINCT se.name, se.stock_entry_type, se.purpose
        FROM `tabStock Entry` se
        LEFT JOIN `tabStock Entry Type` setype ON se.stock_entry_type = setype.name
        WHERE
            se.docstatus < 2
            AND (
                se.purpose = 'Repack'
                OR setype.purpose = 'Repack'
            )
            AND (
                se.name LIKE %(txt)s
                OR se.stock_entry_type LIKE %(txt)s
            )
        ORDER BY se.modified DESC
        LIMIT %(start)s, %(page_len)s
    """, {
        'txt': '%%%s%%' % txt,
        'start': start,
        'page_len': page_len
    })


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_items_with_t_warehouse(doctype, txt, searchfield, start, page_len, filters):
    """
    Get items from Stock Entry Detail where t_warehouse (target warehouse) is set.

    Args:
        filters: Should contain 'stock_entry' - the Stock Entry record name
    """

    stock_entry = filters.get('stock_entry')

    if not stock_entry:
        return []

    return frappe.db.sql("""
        SELECT DISTINCT sed.item_code, sed.item_name, sed.t_warehouse
        FROM `tabStock Entry Detail` sed
        WHERE
            sed.parent = %(stock_entry)s
            AND sed.t_warehouse IS NOT NULL
            AND sed.t_warehouse != ''
            AND sed.item_code LIKE %(txt)s
        ORDER BY sed.idx
        LIMIT %(start)s, %(page_len)s
    """, {
        'stock_entry': stock_entry,
        'txt': '%%%s%%' % txt,
        'start': start,
        'page_len': page_len
    })


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_items_with_serial_no(doctype, txt, searchfield, start, page_len, filters):
    """
    Get items from Purchase Receipt Item where serial_and_batch_bundle has serial numbers.

    Args:
        filters: Should contain 'purchase_receipt' - the Purchase Receipt record name
    """

    purchase_receipt = filters.get('purchase_receipt')

    if not purchase_receipt:
        return []

    return frappe.db.sql("""
        SELECT DISTINCT pri.item_code, pri.item_name
        FROM `tabPurchase Receipt Item` pri
        WHERE
            pri.parent = %(purchase_receipt)s
            AND pri.serial_and_batch_bundle IS NOT NULL
            AND pri.serial_and_batch_bundle != ''
            AND EXISTS (
                SELECT 1 FROM `tabSerial and Batch Entry` sbe
                WHERE sbe.parent = pri.serial_and_batch_bundle
                AND sbe.serial_no IS NOT NULL
                AND sbe.serial_no != ''
            )
            AND pri.item_code LIKE %(txt)s
        ORDER BY pri.idx
        LIMIT %(start)s, %(page_len)s
    """, {
        'purchase_receipt': purchase_receipt,
        'txt': '%%%s%%' % txt,
        'start': start,
        'page_len': page_len
    })
