import frappe

def customer_query_conditions(user):
    if not user:
        user = frappe.session.user

    roles = frappe.get_roles(user)

    # All roles who should see everything
    privileged_roles = ["System Manager", "Administrator", "Team Leader","Accounts Manager"]

    # If user has any privileged role → full access
    if any(role in roles for role in privileged_roles):
        return ""

    if "Purchase Manager" in roles:
        return "`tabCustomer`.workflow_state = 'Approved'"

    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")

    if not employee:
        return "1=0"

    return f"""
        (
            `tabCustomer`.custom_rm = '{employee}'
            OR `tabCustomer`.custom_sales_coordinator = '{employee}'
        )
    """