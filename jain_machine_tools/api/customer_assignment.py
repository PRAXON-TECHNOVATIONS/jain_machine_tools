import frappe
from frappe import whitelist

@whitelist()
def link_assign_to(name, description, employees, doctype):

    if isinstance(employees, str):
        import json
        employees = json.loads(employees)

    users = []

    # employee -> user
    for emp in employees:
        user = frappe.db.get_value("Employee", emp, "user_id")
        if user:
            users.append(user)

    # existing assignments
    todos = frappe.get_all(
        "ToDo",
        filters={
            "reference_type": doctype,
            "reference_name": name
        },
        fields=["name", "allocated_to"]
    )

    existing_users = [d.allocated_to for d in todos]

    # remove old assignments
    for d in todos:
        if d.allocated_to not in users:
            frappe.delete_doc("ToDo", d.name, force=1)

    # add new assignments
    for user in users:
        if user not in existing_users:
            frappe.get_doc({
                "doctype": "ToDo",
                "allocated_to": user,
                "reference_type": doctype,
                "reference_name": name,
                "description": description
            }).insert(ignore_permissions=True)

    return "Assignments Updated"