import frappe
from frappe import _
from frappe.utils import getdate


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "fieldname": "name",
            "label": _("Sales Order / Delivery Planning Schedule"),
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "fieldname": "action",
            "label": _("Create Invoice"),
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "fieldname": "print_action",
            "label": _("Print"),
            "fieldtype": "Data",
            "width": 110,
        },
        {
            "fieldname": "customer",
            "label": _("Customer"),
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "fieldname": "item_code",
            "label": _("Item"),
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "fieldname": "delivery_date",
            "label": _("Delivery Date"),
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "fieldname": "overall_status",
            "label": _("Delivery plan status"),
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "fieldname": "warehouse",
            "label": _("Warehouse"),
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "fieldname": "so_qty",
            "label": _("SO Qty"),
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "fieldname": "planned_qty",
            "label": _("Planned Qty"),
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "fieldname": "status",
            "label": _("Item delivery status"),
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "fieldname": "actual_qty",
            "label": _("Actual Qty"),
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "fieldname": "projected_qty",
            "label": _("Projected Qty"),
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "fieldname": "store_manager_remarks",
            "label": _("Store Manager Remarks"),
            "fieldtype": "Data",
            "width": 220,
        },
    ]


def get_status_html(status):
    if not status:
        return ""
        
    status_lower = status.lower()
    
    # Map your statuses to Frappe's indicator colors
    color_map = {
        "pending": "yellow",
        "partial": "orange",
        "completed": "green"
    }
    
    color = color_map.get(status_lower, "gray") # fallback to gray if another status creeps in
    
    # Frappe standard HTML pill wrapper
    return f'<span class="indicator-pill {color}">{status}</span>'


def get_store_manager_remark_select():
    if frappe.db.has_column("Delivery Planning Schedule", "store_manager_remarks"):
        return "dps.store_manager_remarks"

    if frappe.db.has_column("Delivery Planning Schedule", "store_manager_remark"):
        return "dps.store_manager_remark AS store_manager_remarks"

    return "'' AS store_manager_remarks"


def get_data(filters=None):
    filters = filters or {}
    conditions = ""
    values = {}
    store_manager_remark_select = get_store_manager_remark_select()

    if filters.get("from_date"):
        conditions += " AND dps.schedule_date >= %(from_date)s"
        values["from_date"] = getdate(filters["from_date"])

    if filters.get("to_date"):
        conditions += " AND dps.schedule_date <= %(to_date)s"
        values["to_date"] = getdate(filters["to_date"])

    if filters.get("sales_order"):
        conditions += " AND dps.sales_order = %(sales_order)s"
        values["sales_order"] = filters["sales_order"]

    dps_list = frappe.db.sql(
        f"""
        SELECT
            dps.name,
            dps.sales_order,
            dps.customer,
            dps.status,
            {store_manager_remark_select}
        FROM
            `tabDelivery Planning Schedule` dps
        WHERE 1=1 {conditions}
        ORDER BY dps.sales_order, dps.name
        """,
        values,
        as_dict=True,
    )

    if not dps_list:
        return []

    # Fetch all child items for these DPS docs
    dps_names = [d.name for d in dps_list]
    child_items = frappe.db.sql(
        """
        SELECT
            parent,
            item_code,
            warehouse,
            planned_qty,
            qty_from_so,
            delivery_date,
            status,
            actual_qty,
            projected_qty
        FROM
            `tabDelivery Planning Schedule Item`
        WHERE
            parent IN %(parents)s
        ORDER BY idx
        """,
        {"parents": dps_names},
        as_dict=True,
    )

    # Map children by parent
    children_map = {}
    for item in child_items:
        children_map.setdefault(item.parent, []).append(item)

    # Group DPS docs by Sales Order
    so_map = {}
    for doc in dps_list:
        so_map.setdefault(doc.sales_order, []).append(doc)

    data = []

    for so_name, docs in so_map.items():
        # Sales Order root row
        data.append(
            {
                "name": f'<a href="/app/sales-order/{so_name}">{so_name}</a>',
                "customer": f'<a href="/app/customer/{docs[0].customer}">{docs[0].customer}</a>',
                "item_code": "",
                "delivery_date": "",
                "overall_status": "",
                "warehouse": "",
                "so_qty": "",
                "planned_qty": "",
                "actual_qty": "",
                "projected_qty": "",
                "store_manager_remarks": "",
                "status": "",
                "print_action": "",
                "indent": 0,
            }
        )

        for doc in docs:
            # Delivery Planning Schedule row
            create_btn = (
                f'<button class="btn btn-xs btn-primary jmt-create-invoice-btn" '
                f'data-dps="{doc.name}" data-so="{doc.sales_order}">'
                f'Create Invoice</button>'
            )
            print_btn = (
                f'<div style="text-align: center;">'
                f'<button class="btn btn-xs jmt-print-dps-btn" '
                f'style="background: #000; color: #fff; border-color: #000; min-width: 72px;" '
                f'data-dps="{doc.name}">'
                f'Print</button>'
                f'</div>'
            )
            data.append(
                {
                    "name": f'<a href="/app/delivery-planning-schedule/{doc.name}">{doc.name}</a>',
                    "customer": "",
                    "item_code": "",
                    "delivery_date": "",
                    "overall_status": get_status_html(doc.status),
                    "warehouse": "",
                    "so_qty": "",
                    "planned_qty": "",
                    "actual_qty": "",
                    "projected_qty": "",
                    "store_manager_remarks": doc.store_manager_remarks or "",
                    "status": "",
                    "action": create_btn,
                    "print_action": print_btn,
                    "indent": 1,
                }
            )

            # Child item rows
            for item in children_map.get(doc.name, []):
                data.append(
                    {
                        "name": "",
                        "customer": "",
                        "item_code": f'<a href="/app/item/{item.item_code}">{item.item_code}</a>',
                        "delivery_date": str(item.delivery_date) if item.delivery_date else "",
                        "overall_status": "",
                        "warehouse": item.warehouse or "",
                        "so_qty": item.qty_from_so,
                        "planned_qty": item.planned_qty,
                        "actual_qty": item.actual_qty,
                        "projected_qty": item.projected_qty,
                        "store_manager_remarks": "",
                        "status": get_status_html(item.status), # <-- Colored pill here
                        "print_action": "",
                        "indent": 2,
                    }
                )

    return data


@frappe.whitelist()
def make_sales_invoice(dps_name):
    """
    Map Sales Order → Sales Invoice and pre-fill the Delivery Plans
    connection table with items from the given Delivery Planning Schedule.
    Returns the unsaved doc so the JS can open it in the form view.
    """
    from jain_machine_tools.overrides.sales_order import make_sales_invoice as _make_si

    dps = frappe.get_doc("Delivery Planning Schedule", dps_name)

    # Map Sales Order → Sales Invoice using ERPNext standard mapper
    doc = _make_si(dps.sales_order)

    # Pre-fill the Delivery Plans child table (Connections tab)
    doc.set("delivery_plan_details", [])
    for item in dps.get("items") or []:
        doc.append("delivery_plan_details", {
            "delivery_planning_schedule":      dps_name,
            "delivery_planning_schedule_item": item.name,
            "sales_order_item":                item.sales_order_item,
            "item_code":                       item.item_code,
            "delivery_date":                   item.delivery_date,
            "planned_qty":                     item.planned_qty,
            "qty":                             item.planned_qty,
            "uom":                             item.uom,
        })

    return doc
