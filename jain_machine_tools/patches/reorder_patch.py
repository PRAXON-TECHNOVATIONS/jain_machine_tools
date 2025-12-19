import frappe
from erpnext.stock import reorder_item as erp_reorder

def apply_reorder_patch():
    """
    Monkey patch ERPNext's create_material_request function
    so that custom field 'custom_custom_material_request_type' is set to 'Reorder'
    whenever reorder creates Material Requests.
    Logs and msgprints added for debugging.
    """

    # Save original function
    _original_create_material_request = erp_reorder.create_material_request

    def patched_create_material_request(material_requests):
        # Log patch call
        frappe.log_error("Patched create_material_request called!", "Reorder Patch")
        frappe.msgprint("[Reorder Patch] create_material_request triggered", alert=True)

        # Call original ERPNext function
        mr_list = _original_create_material_request(material_requests)

        if not mr_list:
            frappe.log_error("No Material Requests created by reorder.", "Reorder Patch")
            frappe.msgprint("[Reorder Patch] No MRs created", alert=True)
        else:
            for mr in mr_list:
                try:
                    # Set custom field
                    frappe.db.set_value(
                        "Material Request",
                        mr.name,
                        "custom_custom_material_request_type",
                        "Reorder"
                    )
                    frappe.db.commit()

                    # Log success
                    frappe.log_error(f"Custom field set for MR: {mr.name}", "Reorder Patch")
                    frappe.msgprint(f"[Reorder Patch] MR {mr.name} created and 'Reorder' set", alert=True)

                except Exception as e:
                    frappe.log_error(frappe.get_traceback(), f"Error setting custom field for MR {mr.name}")
                    frappe.msgprint(f"[Reorder Patch] Error updating MR {mr.name}", alert=True)

        return mr_list

    # Apply patch
    erp_reorder.create_material_request = patched_create_material_request
    frappe.log_error("Reorder patch applied successfully!", "Reorder Patch")
    frappe.msgprint("[Reorder Patch] Patch applied successfully!", alert=True)
