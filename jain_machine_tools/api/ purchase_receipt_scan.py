# Copyright (c) 2026
# License: MIT

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint


@frappe.whitelist()
def scan_purchase_receipt_serial(purchase_receipt: str, serial_no: str):
    """
    Scan a serial number and append/update item row in Purchase Receipt.

    Rules:
    - Purchase Receipt must be Draft
    - Serial must exist and be Active
    - Serial must not be already received
    - Serial must not be already scanned in this PR
    - 1 serial scan = qty 1
    """

    if not purchase_receipt or not serial_no:
        frappe.throw(_("Purchase Receipt and Serial No are required"))

    # Validate Purchase Receipt
    
    pr = frappe.get_doc("Purchase Receipt", purchase_receipt)

    if pr.docstatus != 0:
        frappe.throw(_("Purchase Receipt must be in Draft state"))

    # Validate Serial No
    
    if not frappe.db.exists("Serial No", serial_no):
        frappe.throw(_("Serial No {0} does not exist").format(serial_no))

    serial = frappe.get_doc("Serial No", serial_no)

    if serial.status != "Active":
        frappe.throw(_("Serial No {0} is not Active").format(serial_no))

    if serial.warehouse:
        frappe.throw(
            _("Serial No {0} is already received in warehouse {1}")
            .format(serial_no, serial.warehouse)
        )

    item_code = serial.item_code
    if not item_code:
        frappe.throw(_("Item not linked with Serial No {0}").format(serial_no))

    # Prevent duplicate serial in same PR

    for row in pr.items:
        if row.serial_no:
            existing_serials = [
                s.strip() for s in row.serial_no.split("\n") if s.strip()
            ]
            if serial_no in existing_serials:
                frappe.throw(
                    _("Serial No {0} already scanned in this Purchase Receipt")
                    .format(serial_no)
                )

    # Find or create PR Item row

    pr_item_row = None

    for row in pr.items:
        if row.item_code == item_code:
            pr_item_row = row
            break

    if pr_item_row:
        # Append serial
        serials = (
            pr_item_row.serial_no.split("\n")
            if pr_item_row.serial_no
            else []
        )
        serials.append(serial_no)

        pr_item_row.serial_no = "\n".join(serials)
        pr_item_row.qty = cint(pr_item_row.qty) + 1

    else:
        # Create new row
        new_row = pr.append("items", {})
        new_row.item_code = item_code
        new_row.qty = 1
        new_row.serial_no = serial_no

    # ----------------------------------------------------
    # DO NOT save automatically
    # Let user explicitly save
    # ----------------------------------------------------
    pr.set_missing_values()
    pr.calculate_taxes_and_totals()

    return {
        "status": "success",
        "item_code": item_code,
        "message": _("Serial {0} scanned successfully").format(serial_no),
        "summary": _get_pr_summary(pr),
    }


def _get_pr_summary(pr):
    """
    Item-wise summary for frontend
    """
    summary = []

    for row in pr.items:
        if not row.item_code:
            continue

        serial_count = 0
        if row.serial_no:
            serial_count = len(
                [s for s in row.serial_no.split("\n") if s.strip()]
            )

        summary.append({
            "item_code": row.item_code,
            "qty": row.qty,
            "serial_count": serial_count,
        })

    return summary
