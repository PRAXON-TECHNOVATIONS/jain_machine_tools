import frappe

def supplier_permission(user=None):
    if not user:
        user = frappe.session.user

    roles = frappe.get_roles(user)

    if "Purchase User" in roles and not any(
        r in roles for r in [
            "Administrator",
            "System Manager",
            "Purchase Manager",
            "Purchase Master Manager",
        ]
    ):
        return "`tabSupplier`.workflow_state = 'Approved'"

    return ""   