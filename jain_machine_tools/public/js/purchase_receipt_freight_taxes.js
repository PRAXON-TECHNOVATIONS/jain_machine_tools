frappe.ui.form.on("Purchase Receipt", {
    onload(frm) {
        if (frm.doc.docstatus !== 0 || !frm.doc.name) return;
        if (!frm.doc.items || !frm.doc.items.length) return;

        // Only run if PR is created from a Purchase Order
        let has_po = frm.doc.items.some(item => item.purchase_order);
        if (!has_po) return;

        apply_taxes_based_on_template(frm);
    },

    taxes_and_charges(frm) {
        // Re-apply taxes when template changes
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

function setup_intrastate_taxes(frm) {
    frm.clear_table('taxes');

    // Row 1 - Freight (Actual amount - enter manually)
    let freight_row = frm.add_child('taxes');
    freight_row.charge_type = 'Actual';
    freight_row.account_head = 'Freight and Forwarding Charges - JMT';
    freight_row.description = 'Freight Charges';
    freight_row.rate = 0;
    freight_row.tax_amount = 0;
    freight_row.category = 'Valuation and Total';
    freight_row.add_deduct_tax = 'Add';

    // Row 2 - CGST 9% on Previous Row Total (Net Total + Freight)
    let cgst_row = frm.add_child('taxes');
    cgst_row.charge_type = 'On Previous Row Total';
    cgst_row.account_head = 'Input Tax CGST - JMT';
    cgst_row.description = 'CGST @ 9%';
    cgst_row.rate = 9;
    cgst_row.row_id = 1;
    cgst_row.category = 'Valuation and Total';
    cgst_row.add_deduct_tax = 'Add';

    // Row 3 - SGST 9% on Previous Row Total (Net Total + Freight)
    let sgst_row = frm.add_child('taxes');
    sgst_row.charge_type = 'On Previous Row Total';
    sgst_row.account_head = 'Input Tax SGST - JMT';
    sgst_row.description = 'SGST @ 9%';
    sgst_row.rate = 9;
    sgst_row.row_id = 1;
    sgst_row.category = 'Valuation and Total';
    sgst_row.add_deduct_tax = 'Add';

    frm.refresh_field('taxes');
    frappe.show_alert({ message: 'Intra-state taxes applied (CGST + SGST)', indicator: 'green' });
}

function setup_interstate_taxes(frm) {
    frm.clear_table('taxes');

    // Row 1 - Freight (Actual amount - enter manually)
    let freight_row = frm.add_child('taxes');
    freight_row.charge_type = 'Actual';
    freight_row.account_head = 'Freight and Forwarding Charges - JMT';
    freight_row.description = 'Freight Charges';
    freight_row.rate = 0;
    freight_row.tax_amount = 0;
    freight_row.category = 'Valuation and Total';
    freight_row.add_deduct_tax = 'Add';

    // Row 2 - IGST 18% on Previous Row Total (Net Total + Freight)
    let igst_row = frm.add_child('taxes');
    igst_row.charge_type = 'On Previous Row Total';
    igst_row.account_head = 'Input Tax IGST - JMT';
    igst_row.description = 'IGST @ 18%';
    igst_row.rate = 18;
    igst_row.row_id = 1;
    igst_row.category = 'Valuation and Total';
    igst_row.add_deduct_tax = 'Add';

    frm.refresh_field('taxes');
    frappe.show_alert({ message: 'Inter-state taxes applied (IGST)', indicator: 'blue' });
}