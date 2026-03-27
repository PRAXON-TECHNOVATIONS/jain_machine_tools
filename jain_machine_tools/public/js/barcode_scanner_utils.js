/**
 * Generic Barcode Scanner Utilities for Jain Machine Tools
 */

window.jmt_barcode_scanner = {
    async open_dialog(frm, options) {
        if (typeof Html5Qrcode === "undefined") {
            frappe.throw(__("html5-qrcode not loaded. Run bench build."));
        }

        const items_field = options.items_field || "items";
        const serial_items = [];

        for (const row of frm.doc[items_field] || []) {
            if (!row.item_code || row.qty <= 0) continue;

            const r = await frappe.db.get_value("Item", row.item_code, "has_serial_no");

            if (r?.message?.has_serial_no) {
                const existing_serials = this.get_serial_list(row.serial_no);
                serial_items.push({
                    row,
                    completed: existing_serials.length >= row.qty,
                });
            }
        }

        if (!serial_items.length) {
            frappe.msgprint(__("No serial-tracked items found"));
            return;
        }

        const d = new frappe.ui.Dialog({
            title: options.title || __("Barcode Serial Scan"),
            size: "extra-large",
            fields: [
                {
                    fieldname: "use_camera",
                    fieldtype: "Check",
                    label: __("Use Camera Scanner"),
                    default: 0,
                },
                { fieldname: "item_table", fieldtype: "HTML" },
                { fieldname: "scan_area", fieldtype: "HTML" },
            ],
            primary_action_label: __("Close"),
            primary_action() {
                d.hide();
            },
        });

        d.show();
        this.render_item_table(d, frm, serial_items, options);
    },

    render_item_table(d, frm, items, options) {
        let html = `
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>${__("Select")}</th>
                        <th>${__("Item Code")}</th>
                        <th>${__("Qty")}</th>
                        <th>${__("Status")}</th>
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
                    <td>${obj.completed ? __("Completed") : __("Pending")}</td>
                </tr>
            `;
        });

        html += `
                </tbody>
            </table>
            <button class="btn btn-primary" id="start-scan" style="margin-top:14px;">
                ${__("Start Scan")}
            </button>
        `;

        d.fields_dict.item_table.$wrapper.html(html);

        d.fields_dict.item_table.$wrapper.find("#start-scan").on("click", () => {
            const idx = d.fields_dict.item_table.$wrapper
                .find(".scan-item:checked")
                .first()
                .data("idx");

            if (idx === undefined) {
                frappe.msgprint(__("Select a pending item to scan"));
                return;
            }

            if (d.get_value("use_camera")) {
                this.start_camera_scan(d, frm, items, idx, options);
            } else {
                this.start_gun_scan(d, frm, items, idx, options);
            }
        });
    },

    async start_camera_scan(d, frm, items, idx, options) {
        const obj = items[idx];
        const item = obj.row;
        const required_qty = item.qty;
        const scanned = this.get_serial_list(item.serial_no);

        d.fields_dict.scan_area.$wrapper.html(`
            <div style="display:flex; gap:24px; margin-top:20px;">
                <div style="flex:1;">
                    <h4>${__("Scanning")}: ${item.item_code}</h4>
                    <p>${__("Required Qty")}: <b>${required_qty}</b></p>
                    <p>${__("Scanned")}: <b id="scan-count">${scanned.length}</b></p>
                    <div id="scanner-box" style="width:100%; max-width:520px; border:2px solid #d1d8dd; border-radius:8px; background:#000; margin-top:10px;">
                        <div id="reader"></div>
                    </div>
                    <button class="btn btn-success" id="complete" ${scanned.length === required_qty ? "" : "disabled"} style="margin-top:14px;">
                        ${__("Complete Item")}
                    </button>
                </div>
                <div style="flex:1;">
                    <h5>${__("Scanned Serials")}</h5>
                    <table class="table table-bordered" id="scanned-table">
                        <thead><tr><th style="width:50px;">#</th><th>${__("Serial No")}</th></tr></thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>
        `);

        const count_el = d.fields_dict.scan_area.$wrapper.find("#scan-count");
        const complete_btn = d.fields_dict.scan_area.$wrapper.find("#complete");
        const table_body = d.fields_dict.scan_area.$wrapper.find("#scanned-table tbody");

        const render_scanned = () => {
            table_body.html("");
            scanned.forEach((serial, i) => {
                table_body.append(`<tr><td>${i + 1}</td><td>${serial}</td></tr>`);
            });
        };

        render_scanned();

        const scanner = new Html5Qrcode("reader");
        let is_validating_scan = false;

        await scanner.start(
            { facingMode: "environment" },
            { fps: 10, qrbox: { width: 280, height: 120 }, disableFlip: true },
            async (decodedText) => {
                if (is_validating_scan || scanned.includes(decodedText) || scanned.length >= required_qty) return;

                if (this.is_duplicate_serial_for_same_item(frm, options.items_field, item, decodedText)) {
                    frappe.msgprint(__("This serial number is already used for the same item"));
                    return;
                }

                is_validating_scan = true;
                const is_valid = await (options.validate_serial ? options.validate_serial(item.item_code, decodedText) : this.validate_serial_scan(item.item_code, decodedText));
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
            if (options.on_complete) {
                await options.on_complete(frm, item, scanned);
            } else {
                await this.finalize_scan(frm, item, scanned);
            }
            obj.completed = true;
            frappe.show_alert({ message: __("Scan completed for {0}", [item.item_code]), indicator: "green" });
            d.fields_dict.scan_area.$wrapper.html("");
            this.render_item_table(d, frm, items, options);
            if (!items.some((row) => !row.completed)) {
                frappe.msgprint(__("All items scanned"));
                d.hide();
            }
        });
    },

    start_gun_scan(d, frm, items, idx, options) {
        const obj = items[idx];
        const item = obj.row;
        const required_qty = item.qty;
        const scanned = this.get_serial_list(item.serial_no);

        d.fields_dict.scan_area.$wrapper.html(`
            <div style="display:flex; gap:24px; margin-top:20px;">
                <div style="flex:1;">
                    <h4>${__("Scanning")}: ${item.item_code}</h4>
                    <p>${__("Required Qty")}: <b>${required_qty}</b></p>
                    <p>${__("Scanned")}: <b id="scan-count">${scanned.length}</b></p>
                    <input type="text" id="gun-input" placeholder="${__("Scan barcode here")}" style="width:100%; padding:10px; font-size:16px; margin-top:10px;">
                    <button class="btn btn-success" id="complete" ${scanned.length === required_qty ? "" : "disabled"} style="margin-top:14px;">
                        ${__("Complete Item")}
                    </button>
                </div>
                <div style="flex:1;">
                    <h5>${__("Scanned Serials")}</h5>
                    <table class="table table-bordered" id="scanned-table">
                        <thead><tr><th>#</th><th>${__("Serial No")}</th></tr></thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>
        `);

        const count_el = d.fields_dict.scan_area.$wrapper.find("#scan-count");
        const complete_btn = d.fields_dict.scan_area.$wrapper.find("#complete");
        const table_body = d.fields_dict.scan_area.$wrapper.find("#scanned-table tbody");
        const input = d.fields_dict.scan_area.$wrapper.find("#gun-input");

        const render_scanned = () => {
            table_body.html("");
            scanned.forEach((serial, i) => {
                table_body.append(`<tr><td>${i + 1}</td><td>${serial}</td></tr>`);
            });
        };

        render_scanned();
        input.focus();

        input.on("keydown", async (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                const serial = input.val().trim();
                if (!serial) return;

                if (scanned.includes(serial)) {
                    frappe.msgprint(__("Duplicate serial"));
                    input.val("").focus();
                    return;
                }
                if (this.is_duplicate_serial_for_same_item(frm, options.items_field, item, serial)) {
                    frappe.msgprint(__("This serial number is already used for the same item"));
                    input.val("").focus();
                    return;
                }
                if (scanned.length >= required_qty) {
                    frappe.msgprint(__("Required quantity already scanned"));
                    input.val("").focus();
                    return;
                }

                const is_valid = await (options.validate_serial ? options.validate_serial(item.item_code, serial) : this.validate_serial_scan(item.item_code, serial));
                if (!is_valid) {
                    input.val("").focus();
                    return;
                }

                scanned.push(serial);
                count_el.text(scanned.length);
                render_scanned();
                input.val("").focus();
                if (scanned.length === required_qty) complete_btn.prop("disabled", false);
            }
        });

        complete_btn.on("click", async () => {
            if (options.on_complete) {
                await options.on_complete(frm, item, scanned);
            } else {
                await this.finalize_scan(frm, item, scanned);
            }
            obj.completed = true;
            frappe.show_alert({ message: __("Scan completed for {0}", [item.item_code]), indicator: "green" });
            d.fields_dict.scan_area.$wrapper.html("");
            this.render_item_table(d, frm, items, options);
            if (!items.some((row) => !row.completed)) {
                frappe.msgprint(__("All items scanned"));
                d.hide();
            }
        });
    },

    async finalize_scan(frm, item, scanned) {
        item.use_serial_batch_fields = 1;
        item.serial_no = scanned.join("\n");
        item.qty = scanned.length;
        frm.refresh_field("items");
        frm.dirty();
        if (frm.trigger) await frm.trigger("calculate_taxes_and_totals");
    },

    get_serial_list(serial_no) {
        return (serial_no || "").split("\n").map(v => v.trim()).filter(Boolean);
    },

    is_duplicate_serial_for_same_item(frm, items_field, current_item, serial_no) {
        const item_rows = frm.doc[items_field || "items"] || [];
        return item_rows.some((row) => {
            if (!row || row.name === current_item.name || row.item_code !== current_item.item_code) {
                return false;
            }

            return this.get_serial_list(row.serial_no).includes(serial_no);
        });
    },

    async validate_serial_scan(item_code, serial_no) {
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
};
