import frappe

def purchase_order_permission(user=None):
    if not user:
        user = frappe.session.user

    roles = frappe.get_roles(user)

    if "Accounts Manager" in roles and not any(
        r in roles for r in [
            "Administrator",
            "System Manager",
            "Purchase Manager",
            "Purchase Master Manager",
        ]
    ):
        return "`tabPurchase Order`.workflow_state = 'Approved'"

    return ""