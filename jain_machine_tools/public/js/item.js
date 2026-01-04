frappe.ui.form.on('Item', {
    refresh: function(frm) {
        toggle_is_non_standard_field(frm);
    },

    item_group: function(frm) {
        toggle_is_non_standard_field(frm);
    }
});

function toggle_is_non_standard_field(frm) {
    if (!frm.doc.item_group) {
        frm.set_df_property('is_non_standard', 'hidden', 1);
        return;
    }

    // Fetch the parent_item_group for the selected item_group
    frappe.db.get_value('Item Group', frm.doc.item_group, 'parent_item_group')
        .then(r => {
            if (r && r.message && r.message.parent_item_group) {
                const parent_group = r.message.parent_item_group;

                // Check if parent_item_group is "ELECTRIC MOTOR" (case-insensitive)
                if (parent_group.toUpperCase() === 'ELECTRIC MOTOR') {
                    frm.set_df_property('is_non_standard', 'hidden', 0);
                } else {
                    frm.set_df_property('is_non_standard', 'hidden', 1);
                }
            } else {
                // No parent group, hide the field
                frm.set_df_property('is_non_standard', 'hidden', 1);
            }
        });
}
