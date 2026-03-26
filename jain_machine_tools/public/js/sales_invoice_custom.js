frappe.ui.form.on('Sales Invoice', {
    onload: function(frm) {
        frm.set_value('update_stock', 1);
        toggle_delivery_plan_section(frm);
    },

    refresh(frm) {
        if (!frm.doc.update_stock) {
            frm.set_value("update_stock", 1);
        }
        toggle_delivery_plan_section(frm);
        add_delivery_plan_button(frm);
        maybe_load_delivery_plans(frm);

        if (frm.doc.docstatus !== 0 || !frm.doc.name) return;
        if (frm.__barcode_scan_added) return;

        frm.add_custom_button(
            __("Barcode Scan"),
            () => open_sales_invoice_barcode_scan_dialog(frm),
            __("Actions")
        );

        frm.__barcode_scan_added = true;
    },
    sales_order: function(frm) {
        toggle_delivery_plan_section(frm);
        maybe_load_delivery_plans(frm);
    },
    items_add: function(frm) {
        maybe_load_delivery_plans(frm);
    },
    delivery_plan_details_remove: function(frm) {
        sync_invoice_qty_from_delivery_plans(frm);
    }
});

frappe.ui.form.on('Sales Invoice Delivery Plan', {
    qty: function(frm) {
        sync_invoice_qty_from_delivery_plans(frm);
    }
});

frappe.ui.form.on('Sales Invoice Item', {
    item_code: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.item_code) {
            return;
        }

        frappe.model.set_value(cdt, cdn, 'handling_charges_type', '');
        frappe.model.set_value(cdt, cdn, 'handling_charges_percentage', 0);
        frappe.model.set_value(cdt, cdn, 'handling_charges_amount', 0);
        frappe.model.set_value(cdt, cdn, 'base_rate_before_handling_charges', 0);
    },

    rate: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.handling_charges_type) {
            frappe.model.set_value(cdt, cdn, 'base_rate_before_handling_charges', flt(row.rate));
        }
    },

    handling_charges_type: function(frm, cdt, cdn) {
        sync_sales_invoice_item_base_rate(cdt, cdn);
    },

    handling_charges_percentage: function(frm, cdt, cdn) {
        sync_sales_invoice_item_base_rate(cdt, cdn);
    },

    handling_charges_amount: function(frm, cdt, cdn) {
        sync_sales_invoice_item_base_rate(cdt, cdn);
    }
});

function toggle_delivery_plan_section(frm) {
    if (!frm.fields_dict.delivery_plan_details) {
        return;
    }

    frm.set_df_property('delivery_plan_section', 'hidden', 0);
    frm.set_df_property(
        'delivery_plan_details',
        'description',
        'Optional. Select Delivery Plan rows only when this invoice should be linked to Delivery Planning Schedule.'
    );
}

function add_delivery_plan_button(frm) {
    if (!resolve_sales_order(frm) || !frm.fields_dict.delivery_plan_details) {
        return;
    }

    frm.add_custom_button(__('Load Delivery Plans'), () => {
        load_delivery_plans(frm, true);
    });
}

function maybe_load_delivery_plans(frm) {
    if ((frm.doc.delivery_plan_details || []).length) {
        return;
    }

    if (!resolve_sales_order(frm)) {
        return;
    }

    load_delivery_plans(frm, false);
}

function load_delivery_plans(frm, notify) {
    const sales_order = resolve_sales_order(frm);
    if (!sales_order) {
        return;
    }

    frappe.call({
        method: 'jain_machine_tools.overrides.sales_invoice.get_available_delivery_plan_rows',
        args: {
            sales_order: sales_order,
            sales_invoice: frm.doc.name || null
        },
        callback(r) {
            const rows = r.message || [];
            frm.clear_table('delivery_plan_details');

            rows.forEach((row) => {
                const child = frm.add_child('delivery_plan_details');
                child.delivery_planning_schedule = row.delivery_planning_schedule;
                child.delivery_planning_schedule_item = row.delivery_planning_schedule_item;
                child.sales_order_item = row.sales_order_item;
                child.item_code = row.item_code;
                child.delivery_date = row.delivery_date;
                child.planned_qty = row.planned_qty;
                child.already_invoiced_qty = row.already_invoiced_qty;
                child.available_qty = row.available_qty;
                child.qty = row.qty;
                child.uom = row.uom;
            });

            frm.refresh_field('delivery_plan_details');
            sync_invoice_qty_from_delivery_plans(frm);

            if (notify) {
                frappe.show_alert({
                    message: __('Delivery Plan rows loaded'),
                    indicator: 'green'
                });
            }
        }
    });
}

function sync_invoice_qty_from_delivery_plans(frm) {
    const qtyBySoItem = {};
    (frm.doc.delivery_plan_details || []).forEach((row) => {
        if (!row.sales_order_item) {
            return;
        }

        qtyBySoItem[row.sales_order_item] = (qtyBySoItem[row.sales_order_item] || 0) + flt(row.qty);
    });

    (frm.doc.items || []).forEach((row) => {
        if (!row.so_detail) {
            return;
        }

        const qty = qtyBySoItem[row.so_detail] || 0;
        frappe.model.set_value(row.doctype, row.name, 'qty', qty);
    });
}

function resolve_sales_order(frm) {
    if (frm.doc.sales_order) {
        return frm.doc.sales_order;
    }

    for (const row of (frm.doc.items || [])) {
        if (row.sales_order) {
            return row.sales_order;
        }
    }

    return null;
}

function sync_sales_invoice_item_base_rate(cdt, cdn) {
    const row = locals[cdt][cdn];
    if (!row) {
        return;
    }

    if (!row.handling_charges_type) {
        frappe.model.set_value(cdt, cdn, 'base_rate_before_handling_charges', flt(row.rate));
    }
}

async function open_sales_invoice_barcode_scan_dialog(frm) {
    if (typeof Html5Qrcode === "undefined") {
        frappe.throw("html5-qrcode not loaded. Run bench build.");
    }

    const serial_items = [];

    for (const row of frm.doc.items || []) {
        if (!row.item_code || row.qty <= 0) continue;

        const r = await frappe.db.get_value(
            "Item",
            row.item_code,
            "has_serial_no"
        );

        if (r?.message?.has_serial_no) {
            const existing_serials = get_serial_list(row.serial_no);
            serial_items.push({
                row,
                completed: existing_serials.length >= row.qty,
            });
        }
    }

    if (!serial_items.length) {
        frappe.msgprint("No serial-tracked items found");
        return;
    }

    const d = new frappe.ui.Dialog({
        title: "Barcode Serial Scan",
        size: "extra-large",
        fields: [
            {
                fieldname: "use_camera",
                fieldtype: "Check",
                label: "Use Camera Scanner",
                default: 0,
            },
            { fieldname: "item_table", fieldtype: "HTML" },
            { fieldname: "scan_area", fieldtype: "HTML" },
        ],
        primary_action_label: "Close",
        primary_action() {
            d.hide();
        },
    });

    d.show();
    render_sales_invoice_item_table(d, frm, serial_items);
}

function render_sales_invoice_item_table(d, frm, items) {
    let html = `
        <table class="table table-bordered">
            <thead>
                <tr>
                    <th>Select</th>
                    <th>Item Code</th>
                    <th>Qty</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
    `;

    items.forEach((obj, i) => {
        html += `
            <tr>
                <td>
                    <input type="checkbox"
                        class="scan-item"
                        data-idx="${i}"
                        ${obj.completed ? "disabled" : ""}>
                </td>
                <td>${obj.row.item_code}</td>
                <td>${obj.row.qty}</td>
                <td>${obj.completed ? "Completed" : "Pending"}</td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>

        <button class="btn btn-primary"
                id="start-scan"
                style="margin-top:14px;">
            Start Scan
        </button>
    `;

    d.fields_dict.item_table.$wrapper.html(html);

    d.fields_dict.item_table.$wrapper
        .find("#start-scan")
        .on("click", () => {
            const idx = d.fields_dict.item_table.$wrapper
                .find(".scan-item:checked")
                .first()
                .data("idx");

            if (idx === undefined) {
                frappe.msgprint("Select a pending item to scan");
                return;
            }

            if (d.get_value("use_camera")) {
                scan_sales_invoice_item(d, frm, items, idx);
            } else {
                start_sales_invoice_gun_scan(d, frm, items, idx);
            }
        });
}

async function scan_sales_invoice_item(d, frm, items, idx) {
    const obj = items[idx];
    const item = obj.row;
    const required_qty = item.qty;
    const scanned = get_serial_list(item.serial_no);

    d.fields_dict.scan_area.$wrapper.html(`
        <div style="display:flex; gap:24px; margin-top:20px;">
            <div style="flex:1;">
                <h4>Scanning: ${item.item_code}</h4>
                <p>Required Qty: <b>${required_qty}</b></p>
                <p>Scanned: <b id="scan-count">${scanned.length}</b></p>

                <div id="scanner-box"
                     style="
                        width:100%;
                        max-width:520px;
                        border:2px solid #d1d8dd;
                        border-radius:8px;
                        background:#000;
                        margin-top:10px;
                     ">
                    <div id="reader"></div>
                </div>

                <button class="btn btn-success"
                        id="complete"
                        ${scanned.length === required_qty ? "" : "disabled"}
                        style="margin-top:14px;">
                    Complete Item
                </button>
            </div>

            <div style="flex:1;">
                <h5>Scanned Serials</h5>
                <table class="table table-bordered" id="scanned-table">
                    <thead>
                        <tr>
                            <th style="width:50px;">#</th>
                            <th>Serial No</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        </div>
    `);

    const count_el = d.fields_dict.scan_area.$wrapper.find("#scan-count");
    const complete_btn = d.fields_dict.scan_area.$wrapper.find("#complete");
    const table_body = d.fields_dict.scan_area.$wrapper.find(
        "#scanned-table tbody"
    );

    function render_scanned() {
        table_body.html("");
        scanned.forEach((serial, i) => {
            table_body.append(`
                <tr>
                    <td>${i + 1}</td>
                    <td>${serial}</td>
                </tr>
            `);
        });
    }

    render_scanned();

    const scanner = new Html5Qrcode("reader");
    let is_validating_scan = false;

    await scanner.start(
        { facingMode: "environment" },
        {
            fps: 10,
            qrbox: { width: 280, height: 120 },
            disableFlip: true,
        },
        async (decodedText) => {
            if (is_validating_scan) return;
            if (scanned.includes(decodedText)) return;
            if (scanned.length >= required_qty) return;

            is_validating_scan = true;

            const is_valid = await validate_sales_invoice_serial_scan(
                item.item_code,
                decodedText
            );

            is_validating_scan = false;

            if (!is_valid) return;

            scanned.push(decodedText);
            count_el.text(scanned.length);
            render_scanned();

            if (scanned.length === required_qty) {
                complete_btn.prop("disabled", false);
                scanner.stop();
            }
        }
    );

    complete_btn.on("click", async () => {
        await finalize_sales_invoice_scan(frm, item, scanned);
        obj.completed = true;
        frappe.msgprint(`Scan completed for ${item.item_code}`);

        d.fields_dict.scan_area.$wrapper.html("");
        render_sales_invoice_item_table(d, frm, items);

        if (!items.some((row) => !row.completed)) {
            frappe.msgprint("All items scanned");
            d.hide();
        }
    });
}

function start_sales_invoice_gun_scan(d, frm, items, idx) {
    const obj = items[idx];
    const item = obj.row;
    const required_qty = item.qty;
    const scanned = get_serial_list(item.serial_no);

    d.fields_dict.scan_area.$wrapper.html(`
        <div style="display:flex; gap:24px; margin-top:20px;">
            <div style="flex:1;">
                <h4>Scanning: ${item.item_code}</h4>
                <p>Required Qty: <b>${required_qty}</b></p>
                <p>Scanned: <b id="scan-count">${scanned.length}</b></p>

                <input type="text"
                    id="gun-input"
                    placeholder="Scan barcode here"
                    style="width:100%; padding:10px; font-size:16px; margin-top:10px;">

                <button class="btn btn-success"
                        id="complete"
                        ${scanned.length === required_qty ? "" : "disabled"}
                        style="margin-top:14px;">
                    Complete Item
                </button>
            </div>

            <div style="flex:1;">
                <h5>Scanned Serials</h5>
                <table class="table table-bordered" id="scanned-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Serial No</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        </div>
    `);

    const count_el = d.fields_dict.scan_area.$wrapper.find("#scan-count");
    const complete_btn = d.fields_dict.scan_area.$wrapper.find("#complete");
    const table_body = d.fields_dict.scan_area.$wrapper.find(
        "#scanned-table tbody"
    );
    const input = d.fields_dict.scan_area.$wrapper.find("#gun-input");

    function render_scanned() {
        table_body.html("");
        scanned.forEach((serial, i) => {
            table_body.append(`
                <tr>
                    <td>${i + 1}</td>
                    <td>${serial}</td>
                </tr>
            `);
        });
    }

    render_scanned();
    input.focus();

    input.on("keydown", async function (e) {
        if (e.key === "Enter") {
            e.preventDefault();

            const serial = $(this).val().trim();

            if (!serial) return;

            if (scanned.includes(serial)) {
                frappe.msgprint("Duplicate serial");
                $(this).val("");
                return;
            }

            if (scanned.length >= required_qty) {
                frappe.msgprint("Required quantity already scanned");
                $(this).val("");
                return;
            }

            const is_valid = await validate_sales_invoice_serial_scan(
                item.item_code,
                serial
            );

            if (!is_valid) {
                $(this).val("");
                $(this).focus();
                return;
            }

            scanned.push(serial);
            count_el.text(scanned.length);
            render_scanned();
            $(this).val("");

            if (scanned.length === required_qty) {
                complete_btn.prop("disabled", false);
            }

            $(this).focus();
        }
    });

    complete_btn.on("click", async () => {
        await finalize_sales_invoice_scan(frm, item, scanned);
        obj.completed = true;

        frappe.msgprint(`Scan completed for ${item.item_code}`);

        d.fields_dict.scan_area.$wrapper.html("");
        render_sales_invoice_item_table(d, frm, items);

        if (!items.some((row) => !row.completed)) {
            frappe.msgprint("All items scanned");
            d.hide();
        }
    });
}

async function finalize_sales_invoice_scan(frm, item, scanned) {
    item.use_serial_batch_fields = 1;
    item.serial_no = scanned.join("\n");
    item.qty = scanned.length;

    frm.refresh_field("items");
    frm.dirty();
    await frm.trigger("calculate_taxes_and_totals");
}

function get_serial_list(serial_no) {
    return (serial_no || "")
        .split("\n")
        .map((value) => value.trim())
        .filter(Boolean);
}

async function validate_sales_invoice_serial_scan(item_code, serial_no) {
    const response = await frappe.db.get_value(
        "Serial No",
        { name: serial_no },
        ["name", "item_code"]
    );

    const serial_doc = response?.message;

    if (!serial_doc?.name || serial_doc.item_code !== item_code) {
        frappe.msgprint({
            title: __("Invalid Scan"),
            indicator: "red",
            message: __("Scan actual item code"),
        });
        return false;
    }

    return true;
}
