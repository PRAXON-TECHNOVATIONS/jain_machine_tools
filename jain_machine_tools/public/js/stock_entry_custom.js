frappe.ui.form.on('Stock Entry', {
    onload: function(frm) {
        set_in_transit_for_material_transfer(frm);
        setup_destination_warehouse_dropdown(frm);
    },
    refresh: function(frm) {
        set_in_transit_for_material_transfer(frm);
        setup_destination_warehouse_dropdown(frm);
        add_barcode_scan_button(frm);
    },
    purpose: function(frm) {
        set_in_transit_for_material_transfer(frm);
        setup_destination_warehouse_dropdown(frm);
    },
    stock_entry_type: function(frm) {
        add_barcode_scan_button(frm);
    }
});

function add_barcode_scan_button(frm) {
    if (frm.doc.stock_entry_type === 'Material Transfer' && frm.doc.docstatus === 0 && frm.doc.name) {
        if (frm.__barcode_scan_added) return;

        frm.add_custom_button(
            __('Barcode Scan'),
            () => window.jmt_barcode_scanner.open_dialog(frm, {
                title: __('Stock Entry Barcode Scan'),
                items_field: 'items',
                get_warehouse(frm, item) {
                    return resolve_stock_entry_scan_warehouse(frm, item);
                },
                async validate_serial(item, serial_no, frm, warehouse) {
                    return window.jmt_barcode_scanner.validate_serial_scan(
                        item.item_code,
                        serial_no,
                        warehouse || resolve_stock_entry_scan_warehouse(frm, item)
                    );
                },
                async on_complete(frm, item, scanned) {
                    item.use_serial_batch_fields = 1;
                    item.serial_no = scanned.join('\n');
                    item.qty = scanned.length;

                    frm.refresh_field('items');
                    frm.dirty();
                }
            }),
            __('Actions')
        );

        frm.__barcode_scan_added = true;
    } else {
        frm.remove_custom_button(__('Barcode Scan'), __('Actions'));
        delete frm.__barcode_scan_added;
    }
}

function set_in_transit_for_material_transfer(frm) {
    if (frm.doc.purpose === 'Material Transfer' && !frm.doc.add_to_transit) {
        frm.set_value('add_to_transit', 1);
    }
}

function setup_destination_warehouse_dropdown(frm) {
    const fieldname = 'destination_warehouse_select';
    if (!frm.fields_dict[fieldname] || frm.doc.purpose !== 'Material Transfer') {
        return;
    }

    frm.set_query(fieldname, function() {
        return {
            query: 'jain_machine_tools.api.stock_entry.get_warehouse_names_query'
        };
    });
}

function resolve_stock_entry_scan_warehouse(frm, item) {
    return item.s_warehouse || frm.doc.from_warehouse || frm.doc.set_warehouse || null;
}
