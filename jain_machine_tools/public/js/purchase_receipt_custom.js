frappe.ui.form.on("Purchase Receipt", {
    refresh(frm) {
        if (frm.doc.docstatus !== 0 || !frm.doc.name) return;
        if (frm.__barcode_scan_added) return;

        frm.add_custom_button(
            __("Barcode Scan"),
            () => open_barcode_scan_dialog(frm),
            __("Actions")
        );

        frm.__barcode_scan_added = true;
    },
});

async function open_barcode_scan_dialog(frm) {
    if (typeof Html5Qrcode === "undefined") {
        frappe.throw("html5-qrcode not loaded. Run bench build.");
    }

    const serial_items = [];

    for (const row of frm.doc.items) {
        if (!row.item_code || row.qty <= 0) continue;

        const r = await frappe.db.get_value(
            "Item",
            row.item_code,
            "has_serial_no"
        );

        if (r?.message?.has_serial_no) {
            serial_items.push({
                row,
                completed: !!row.serial_no
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
            default: 0
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
    render_item_table(d, frm, serial_items);
}

function get_serial_list(serial_no) {
    return (serial_no || "").split("\n").map((value) => value.trim()).filter(Boolean);
}

function is_duplicate_serial_for_same_item(frm, current_item, serial_no) {
    return (frm.doc.items || []).some((row) => {
        if (!row || row.name === current_item.name || row.item_code !== current_item.item_code) {
            return false;
        }

        return get_serial_list(row.serial_no).includes(serial_no);
    });
}

async function validate_serial_scan(item_code, serial_no) {
    const r = await frappe.db.get_value("Serial No", { name: serial_no }, ["name", "item_code"]);
    const serial_doc = r?.message;

    if (!serial_doc?.name || serial_doc.item_code !== item_code) {
        frappe.msgprint({
            title: __("Invalid Scan"),
            indicator: "red",
            message: __("Enter valid Serial number"),
        });
        return false;
    }

    return true;
}

// ITEM TABLE

function render_item_table(d, frm, items) {
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
            // CAMERA MODE
            scan_item(d, frm, items, idx);
        } else {
            // BARCODE GUN MODE
            start_gun_scan(d, frm, items, idx);
        }
    });
}

// SCAN SINGLE ITEM

async function scan_item(d, frm, items, idx) {
    const obj = items[idx];
    const item = obj.row;
    const required_qty = item.qty;
    const scanned = [];

    d.fields_dict.scan_area.$wrapper.html(`
        <div style="display:flex; gap:24px; margin-top:20px;">
            
            <!-- LEFT -->
            <div style="flex:1;">
                <h4>Scanning: ${item.item_code}</h4>
                <p>Required Qty: <b>${required_qty}</b></p>
                <p>Scanned: <b id="scan-count">0</b></p>

                <!-- SIMPLE CAMERA BOX -->
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
                        disabled
                        style="margin-top:14px;">
                    Complete Item
                </button>
            </div>

            <!-- RIGHT -->
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
    const table_body = d.fields_dict.scan_area.$wrapper
        .find("#scanned-table tbody");

    function render_scanned() {
        table_body.html("");
        scanned.forEach((s, i) => {
            table_body.append(`
                <tr>
                    <td>${i + 1}</td>
                    <td>${s}</td>
                </tr>
            `);
        });
    }

    const scanner = new Html5Qrcode("reader");

    await scanner.start(
        { facingMode: "environment" },
        {
            fps: 10,
            qrbox: { width: 280, height: 120 },
            disableFlip: true,
        },
        (decodedText) => {
            if (scanned.includes(decodedText)) return;
            if (scanned.length >= required_qty) return;
            if (is_duplicate_serial_for_same_item(frm, item, decodedText)) {
                frappe.msgprint(__("This serial number is already used for the same item"));
                return;
            }

            validate_serial_scan(item.item_code, decodedText).then((is_valid) => {
                if (!is_valid) return;

                scanned.push(decodedText);
                count_el.text(scanned.length);
                render_scanned();

                if (scanned.length === required_qty) {
                    complete_btn.prop("disabled", false);
                    scanner.stop();
                }
            });
        }
    );

    complete_btn.on("click", () => {
        item.use_serial_batch_fields = 1;
        item.serial_no = scanned.join("\n");
        item.qty = scanned.length;

        frm.refresh_field("items");
        frm.dirty();

        obj.completed = true;
        frappe.msgprint(`Scan completed for ${item.item_code}`);

        d.fields_dict.scan_area.$wrapper.html("");
        render_item_table(d, frm, items);

        if (!items.some(o => !o.completed)) {
            frappe.msgprint("All items scanned");
            d.hide();
        }
    });
}

function start_gun_scan(d, frm, items, idx) {

    const obj = items[idx];
    const item = obj.row;
    const required_qty = item.qty;
    const scanned = [];

    d.fields_dict.scan_area.$wrapper.html(`
        <div style="display:flex; gap:24px; margin-top:20px;">
            <div style="flex:1;">
                <h4>Scanning: ${item.item_code}</h4>
                <p>Required Qty: <b>${required_qty}</b></p>
                <p>Scanned: <b id="scan-count">0</b></p>

                <input type="text"
                    id="gun-input"
                    placeholder="Scan barcode here"
                    style="width:100%; padding:10px; font-size:16px; margin-top:10px;">

                <button class="btn btn-success"
                        id="complete"
                        disabled
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
    const table_body = d.fields_dict.scan_area.$wrapper.find("#scanned-table tbody");
    const input = d.fields_dict.scan_area.$wrapper.find("#gun-input");

    input.focus();

    input.on("keydown", async function(e) {

        if (e.key === "Enter") {

            e.preventDefault();

            let serial = $(this).val().trim();

            if (!serial) return;

            if (scanned.includes(serial)) {
                frappe.msgprint("Duplicate serial");
                $(this).val("");
                return;
            }
            if (is_duplicate_serial_for_same_item(frm, item, serial)) {
                frappe.msgprint(__("This serial number is already used for the same item"));
                $(this).val("");
                return;
            }
            // qty limit check
            if (scanned.length >= required_qty) {
                frappe.msgprint("Required quantity already scanned");
                $(this).val("");
                return;
            }
            const is_valid = await validate_serial_scan(item.item_code, serial);
            if (!is_valid) {
                $(this).val("");
                return;
            }
            scanned.push(serial);

            count_el.text(scanned.length);

            table_body.append(`
                <tr>
                    <td>${scanned.length}</td>
                    <td>${serial}</td>
                </tr>
            `);

            $(this).val("");

            if (scanned.length === required_qty) {
                complete_btn.prop("disabled", false);
            }

            $(this).focus();
        }

    });
    complete_btn.on("click", () => {
        item.use_serial_batch_fields = 1;
        item.serial_no = scanned.join("\n");
        item.qty = scanned.length;

        frm.refresh_field("items");
        frm.dirty();

        obj.completed = true;

        frappe.msgprint(`Scan completed for ${item.item_code}`);

        d.fields_dict.scan_area.$wrapper.html("");
        render_item_table(d, frm, items);

        if (!items.some(o => !o.completed)) {
            frappe.msgprint("All items scanned");
            d.hide();
        }

    });
}
frappe.ui.form.on("Purchase Receipt", {
    onload(frm) {
        if (frm.doc.docstatus !== 0 || !frm.doc.name) return;
        if (!frm.doc.items || !frm.doc.items.length) return;

        let has_po = frm.doc.items.some(item => item.purchase_order);
        if (!has_po) return;

        apply_taxes_based_on_template(frm);
    },

    taxes_and_charges(frm) {
        let has_po = frm.doc.items && frm.doc.items.some(item => item.purchase_order);
        if (!has_po) return;

        apply_taxes_based_on_template(frm);
    }
});

frappe.ui.form.on('Purchase Taxes and Charges', {
    tax_amount: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.charge_type === 'Actual') {
            frm.trigger('calculate_taxes_and_totals');
        }
    }
});

function apply_taxes_based_on_template(frm) {
    let template = (frm.doc.taxes_and_charges || '').toLowerCase();

    if (template.includes('out') || template.includes('inter') || template.includes('igst')) {
        setup_interstate_taxes(frm);
    } else {
        setup_intrastate_taxes(frm);
    }
}

async function setup_intrastate_taxes(frm) {
    const po_name = frm.doc.items.find(i => i.purchase_order)?.purchase_order;
    if (!po_name) return;

    const po = await frappe.db.get_doc('Purchase Order', po_name);
    if (!po.taxes || !po.taxes.length) return;

    frm.clear_table('taxes');

    // Row 1 - Freight (hardcoded as before)
    let freight_row = frm.add_child('taxes');
    freight_row.charge_type = 'Actual';
    freight_row.account_head = 'Freight Charges - JMT';
    freight_row.description = 'Freight Charges';
    freight_row.rate = 0;
    freight_row.tax_amount = 0;
    freight_row.category = 'Valuation and Total';
    freight_row.add_deduct_tax = 'Add';

    // Row 2 - CGST: account_head, description, rate, tax_amount, category, add_deduct_tax from PO
    const cgst_po = po.taxes.find(r => r.account_head === 'Input Tax CGST - JMT');
    if (cgst_po) {
        let cgst_row = frm.add_child('taxes');
        cgst_row.charge_type    = 'On Previous Row Total';
        cgst_row.row_id         = "1";
        cgst_row.account_head   = cgst_po.account_head;
        cgst_row.description    = cgst_po.description;
        cgst_row.rate           = cgst_po.rate;
        cgst_row.tax_amount     = cgst_po.tax_amount;
        cgst_row.category       = cgst_po.category;
        cgst_row.add_deduct_tax = cgst_po.add_deduct_tax;
    }

    // Row 3 - SGST: account_head, description, rate, tax_amount, category, add_deduct_tax from PO
    const sgst_po = po.taxes.find(r => r.account_head === 'Input Tax SGST - JMT');
    if (sgst_po) {
        let sgst_row = frm.add_child('taxes');
        sgst_row.charge_type    = 'On Previous Row Total';
        sgst_row.row_id         = "1";
        sgst_row.account_head   = sgst_po.account_head;
        sgst_row.description    = sgst_po.description;
        sgst_row.rate           = sgst_po.rate;
        sgst_row.tax_amount     = sgst_po.tax_amount;
        sgst_row.category       = sgst_po.category;
        sgst_row.add_deduct_tax = sgst_po.add_deduct_tax;
    }

    frm.refresh_field('taxes');
    frappe.show_alert({ message: 'Intra-state taxes applied (CGST + SGST)', indicator: 'green' });
}

async function setup_interstate_taxes(frm) {
    const po_name = frm.doc.items.find(i => i.purchase_order)?.purchase_order;
    if (!po_name) return;

    const po = await frappe.db.get_doc('Purchase Order', po_name);
    if (!po.taxes || !po.taxes.length) return;

    frm.clear_table('taxes');

    // Row 1 - Freight (hardcoded as before)
    let freight_row = frm.add_child('taxes');
    freight_row.charge_type = 'Actual';
    freight_row.account_head = 'Freight Charges - JMT';
    freight_row.description = 'Freight Charges';
    freight_row.rate = 0;
    freight_row.tax_amount = 0;
    freight_row.category = 'Valuation and Total';
    freight_row.add_deduct_tax = 'Add';

    // Row 2 - IGST: account_head, description, rate, tax_amount, category, add_deduct_tax from PO
    const igst_po = po.taxes.find(r => r.account_head === 'Input Tax IGST - JMT');
    if (igst_po) {
        let igst_row = frm.add_child('taxes');
        igst_row.charge_type    = 'On Previous Row Total';
        igst_row.row_id         = "1";
        igst_row.account_head   = igst_po.account_head;
        igst_row.description    = igst_po.description;
        igst_row.rate           = igst_po.rate;
        igst_row.tax_amount     = igst_po.tax_amount;
        igst_row.category       = igst_po.category;
        igst_row.add_deduct_tax = igst_po.add_deduct_tax;
    }

    frm.refresh_field('taxes');
    frappe.show_alert({ message: 'Inter-state taxes applied (IGST)', indicator: 'blue' });
}
