# import frappe

# def material_request_permission(user=None):
#     if not user:
#         user = frappe.session.user

#     roles = frappe.get_roles(user)

#     # Agar Purchase User hai aur koi high role nahi hai
#     if "Purchase User" in roles and not any(
#         r in roles for r in [
#             "Administrator",
#             "System Manager",
#             "Purchase Manager",
#             "Purchase Master Manager",
#             "Accounts Manager"
#         ]
#     ):
#         return f"""
#             EXISTS (
#                 SELECT 1 FROM `tabToDo`
#                 WHERE
#                     `tabToDo`.reference_type = 'Material Request'
#                     AND `tabToDo`.reference_name = `tabMaterial Request`.name
#                     AND `tabToDo`.allocated_to = '{user}'
#             )
#         """

#     return ""
