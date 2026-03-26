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
