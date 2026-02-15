"""
Reorder Override - Replace ERPNext's daily reorder with JMT's optimized hourly reorder
"""
import frappe
import erpnext.stock.reorder_item


def set_reorder_field(doc, method):
    """
    Hook Handler for Material Request before_insert
    Sets custom field to identify auto-generated reorder MRs
    """
    if frappe.flags.in_auto_reorder_process:
        doc.custom_custom_material_request_type = "Reorder"


def override_erpnext_reorder(bootinfo=None):
    """
    Override ERPNext's default reorder_item function
    This prevents duplication (daily ERPNext + hourly JMT)

    Args:
        bootinfo: Optional bootinfo dict passed by frappe boot_session hook
    """
    # Replace ERPNext's reorder_item with a no-op function
    # Our optimized version runs hourly from scheduler_events
    def noop_reorder_item():
        """No-op function - JMT's optimized reorder runs hourly instead"""
        frappe.logger().info(
            "ERPNext default daily reorder skipped - using JMT optimized hourly reorder"
        )
        return

    erpnext.stock.reorder_item.reorder_item = noop_reorder_item


# Call override on module load
override_erpnext_reorder()