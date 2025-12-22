import frappe


def populate_supplier_item_code(doc, method=None):
    """
    Auto-populate custom_supplier_code in child table items
    by looking up Party Specific Item for the supplier.

    Used for:
    - Supplier Quotation (items child table)
    - Purchase Order (items child table)
    """

    if not doc.supplier:
        return

    # Get the child table field name based on doctype
    child_table_field = "items"

    for item in doc.get(child_table_field, []):
        if not item.item_code:
            continue

        # Look up Party Specific Item
        supplier_item_code = get_supplier_item_code(doc.supplier, item.item_code)

        if supplier_item_code:
            item.custom_supplier_code = supplier_item_code


def get_supplier_item_code(supplier, item_code):
    """
    Fetch supplier_item_code from Party Specific Item.

    Args:
        supplier: Supplier name
        item_code: Item code

    Returns:
        supplier_item_code if found, else None
    """

    try:
        party_specific_item = frappe.db.get_value(
            "Party Specific Item",
            filters={
                "party_type": "Supplier",
                "party": supplier,
                "based_on_value": item_code
            },
            fieldname="supplier_item_code"
        )

        return party_specific_item

    except Exception as e:
        frappe.log_error(
            title="Error fetching supplier item code",
            message=f"Supplier: {supplier}, Item: {item_code}\n{str(e)}"
        )
        return None
