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

//  ITEM TABLE

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

            scan_item(d, frm, items, idx);
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

            scanned.push(decodedText);
            count_el.text(scanned.length);
            render_scanned();

            if (scanned.length === required_qty) {
                complete_btn.prop("disabled", false);
                scanner.stop();
            }
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


