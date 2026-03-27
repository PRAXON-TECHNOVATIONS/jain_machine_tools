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
            "label": _("Overall Status"),
            "fieldtype": "Data",
            "width": 130,
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
            "label": _("Status"),
            "fieldtype": "Data",
            "width": 130,
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


def get_data(filters=None):
    filters = filters or {}
    conditions = ""
    values = {}

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
            dps.status
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
            planned_qty,
            qty_from_so,
            delivery_date,
            status
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
                "so_qty": "",
                "planned_qty": "",
                "status": "",
                "indent": 0,
            }
        )

        for doc in docs:
            # Delivery Planning Schedule row
            data.append(
                {
                    "name": f'<a href="/app/delivery-planning-schedule/{doc.name}">{doc.name}</a>',
                    "customer": "",
                    "item_code": "",
                    "delivery_date": "",
                    "overall_status": get_status_html(doc.status), # <-- Colored pill here
                    "so_qty": "",
                    "planned_qty": "",
                    "status": "",
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
                        "so_qty": item.qty_from_so,
                        "planned_qty": item.planned_qty,
                        "status": get_status_html(item.status), # <-- Colored pill here
                        "indent": 2,
                    }
                )

    return data