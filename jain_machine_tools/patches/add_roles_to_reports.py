import frappe

def execute():
    # Mapping: report -> list of roles
    report_role_map = {
        "Stock Ledger": ["Store Manager", "Stock User", "Sales Head", "Accounts Manager"],
        "Stock Balance": ["Store Manager", "Stock User", "Stock Manager", "JMT Stock User", "Accounts Manager"],
        "Stock Projected Qty": ["Accounts User", "Item Manager", "JMT Stock User", "Maintenance User", "Manufacturing User", "Purchase User", "Sales User", "Stock Manager", "Stock User"],
        "Stock Ageing": ["Accounts User", "Item Manager", "JMT Stock User", "Maintenance User", "Manufacturing User", "Purchase User", "Sales User", "Stock Manager", "Stock User"],
        "Item Price Stock": ["Accounts User", "Item Manager", "JMT Stock User", "Maintenance User", "Manufacturing User", "Purchase User", "Sales User", "Stock Manager", "Stock User"],
        "Warehouse Wise Stock Balance": ["Accounts Manager", "JMT Stock User", "Stock User"],

        "Purchase Analytics": ["Purchase Manager", "Purchase User"],
        "Purchase Order Analysis": ["Purchase Manager", "Purchase User", "Stock User", "Supplier"],
        "Supplier-Wise Sales Analytics": ["Accounts Manager", "Stock User"],
        "Requested Items to Order and Receive": ["Purchase Manager", "Purchase User", "Stock Manager", "Stock User"],
        "Purchase Order Trends": ["Purchase Manager", "Purchase User", "Stock User"],
        "Procurement Tracker": ["Purchase Manager", "Purchase User"],

        "Items To Be Requested": ["Purchase Manager", "Purchase User", "Stock Manager", "Stock User"],
        "Item-wise Purchase History": ["Purchase Manager", "Purchase User", "Stock User"],
        "Purchase Receipt Trends": ["Accounts User", "Stock Manager", "Purchase User", "Stock User"],
        "Purchase Invoice Trends": ["Accounts Manager", "Accounts User", "Auditor", "Purchase User"],

        "Subcontracted Raw Materials To Be Transferred": ["Purchase Manager", "Purchase User", "Stock User"],
        "Subcontracted Item To Be Received": ["Purchase Manager", "Purchase User", "Stock User"],
        "Supplier Quotation Comparison": ["Manufacturing Manager", "Purchase Manager", "Purchase User", "Stock User"],
        "Material Requests for which Supplier Quotations are not created": ["Stock Manager", "Purchase Manager", "Purchase User", "Stock User"],

        "Address And Contacts": ["Accounts User", "Maintenance User", "Purchase User", "Sales User"],

        "Sales Analytics": ["Sales Manager", "Stock User", "Maintenance User", "Accounts User"],
        "Sales Order Analysis": ["Sales Manager", "Stock User", "Sales User", "Maintenance User", "Accounts User", "Sales Coordinate", "Sales Executive"],
        "Sales Order Trends": ["Sales Manager", "Stock User", "Sales User", "Maintenance User", "Accounts User"],
        "Sales Pipeline Analytics": ["Sales Manager", "Sales User"],
        "Address And Contacts": ["Sales User", "Maintenance User", "Purchase User", "Accounts User"],
        "Customers Without Any Sales Transactions": ["Sales Manager", "Sales User", "System Manager"],
        "Customer Credit Balance": ["Accounts Manager", "Sales Manager", "Sales Master Manager", "Sales User", "Stock Manager", "Stock User"],
        "Item-wise Sales History": ["Sales Manager", "Stock User", "Sales User", "Maintenance User", "Accounts User"],
    }

    for report_name, roles in report_role_map.items():

        if not frappe.db.exists("Report", report_name):
            print(f"❌ Report not found: {report_name}")
            continue

        report = frappe.get_doc("Report", report_name)
        existing_roles = [r.role for r in report.roles]

        updated = False

        for role in roles:
            if role not in existing_roles:
                report.append("roles", {"role": role})
                print(f"✅ Added {role} → {report_name}")
                updated = True
            else:
                print(f"⚠️ Exists {role} → {report_name}")

        if updated:
            report.save(ignore_permissions=True)

    frappe.db.commit()