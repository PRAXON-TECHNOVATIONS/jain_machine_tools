import frappe
import pandas as pd
from frappe.utils.file_manager import get_file

@frappe.whitelist()
def parse_excel(file_url):
    import frappe
    import os
    import pandas as pd

    if not file_url:
        frappe.throw("File URL is required")

    # file_url comes like /private/files/test.xlsx
    # remove leading slash
    file_name = file_url.split("/files/")[-1]

    # build absolute path
    site_path = frappe.get_site_path("private", "files", file_name)

    if not os.path.exists(site_path):
        frappe.throw(f"File not found at: {site_path}")

    # read excel
    df = pd.read_excel(site_path)

    expected = [
        "Item Code",
        "Serial No",
        "Vendor Manufacture Date",
        "Warranty Period (Months)"
    ]

    for col in expected:
        if col not in df.columns:
            frappe.throw(f"Missing required column: {col}")

    rows = []
    for _, row in df.iterrows():
        rows.append({
            "item_code": row["Item Code"],
            "serial_no": row["Serial No"],
            "vendor_mf_date": str(row["Vendor Manufacture Date"]),
            "warranty_months": row["Warranty Period (Months)"]
        })

    return rows

