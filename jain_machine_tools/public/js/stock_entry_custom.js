frappe.ui.form.on('Stock Entry', {
    onload: function(frm) {
        set_in_transit_for_material_transfer(frm);
        setup_destination_warehouse_dropdown(frm);
    },
    refresh: function(frm) {
        set_in_transit_for_material_transfer(frm);
        setup_destination_warehouse_dropdown(frm);
    },
    purpose: function(frm) {
        set_in_transit_for_material_transfer(frm);
        setup_destination_warehouse_dropdown(frm);
    }
});

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
