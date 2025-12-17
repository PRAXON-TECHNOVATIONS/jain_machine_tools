frappe.ui.form.on('Purchase Order', {
    refresh(frm) {
        hide_get_items_from_po(frm);
        hide_tools_po(frm);
    },
    onload(frm) {
        hide_get_items_from_po(frm);
        hide_tools_po(frm);
    },
    after_save(frm) {
        hide_get_items_from_po(frm);
        hide_tools_po(frm);
    }
});

function hide_get_items_from_po(frm) {
    setTimeout(() => {
        [
            'Material Request',
            'Product Bundle'
        ].forEach(btn => {
            frm.remove_custom_button(btn, 'Get Items From');
        });
    }, 200);
}
function hide_tools_po(frm) {
    setTimeout(() => {
        [
            'Update Rate as per Last Purchase',
            'Link to Material Request',
        ].forEach(btn => {
            frm.remove_custom_button(btn, 'Tools');
        });
    }, 200);
}