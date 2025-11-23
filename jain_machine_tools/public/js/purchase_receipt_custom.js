frappe.ui.form.on('Purchase Receipt', {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.docstatus === 0) {
            frm.add_custom_button('Add Serial No', function () {
                show_serial_upload_dialog(frm);
            }, "Actions");
        }
    }
});


function show_serial_upload_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: "Upload Serial No (Excel)",
        size: "large",
        fields: [
            {
                fieldname: "excel",
                label: "Upload Excel",
                fieldtype: "Attach"
            },
            {
                fieldname: "table_area",
                fieldtype: "HTML"
            }
        ],
        primary_action_label: "Process",
        primary_action(values) {
            if (!values.excel) {
                frappe.msgprint("Please upload an Excel file.");
                return;
            }

            frappe.call({
                method: "jain_machine_tools.api.serial_import.parse_excel",
                args: { file_url: values.excel },
                callback: function (r) {
                    if (r.message) {
                        render_serial_table(d, r.message);
                    }
                }
            });
        }
    });

    // empty table initially
    render_serial_table(d, []);
    d.show();
}


function render_serial_table(dialog, rows) {
    let html = `
        <table class="table table-bordered">
            <thead>
                <tr>
                    <th>Item Code</th>
                    <th>Serial No</th>
                    <th>Vendor Manufacture Date</th>
                    <th>Warranty Period (Months)</th>
                </tr>
            </thead>
            <tbody>
    `;

    rows.forEach(r => {
        html += `
            <tr>
                <td>${r.item_code}</td>
                <td>${r.serial_no}</td>
                <td>${r.vendor_mf_date}</td>
                <td>${r.warranty_months}</td>
            </tr>
        `;
    });

    html += `</tbody></table>`;

    dialog.fields_dict.table_area.$wrapper.html(html);
}