// Copyright (c) 2025, Praxon Technovation and contributors
// For license information, please see license.txt

frappe.ui.form.on("Non Standard Item Configurator", {
    base_item(frm) {
        frm.set_query("select_base_price", () => {
            if (!frm.doc.base_item) {
                return {};
            }
            return {
                filters: {
                    item_code: frm.doc.base_item,
                }
            };
        });
    },

    refresh(frm) {
        if (frm.doc.base_item) {
            frm.trigger("base_item");
        }
        if (frm.is_new()) {
            frm.toggle_display("create_item", false);
        } else {
            frm.toggle_display("create_item", true);
        }
    },

    create_item(frm) {
        frappe.call({
            method: "create_item_and_price",
            doc: frm.doc,
            callback: function () {
                frm.reload_doc();
            }
        });
    }
});