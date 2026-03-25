frappe.ui.form.on('Delivery Planning Schedule', {
	refresh(frm) {
		frm.set_query('sales_order', () => ({
			query: 'jain_machine_tools.jain_machine_tools.doctype.delivery_planning_schedule.delivery_planning_schedule.sales_order_query'
		}));

		const is_saved = !frm.is_new();
		frm.toggle_display('get_items', is_saved);
		frm.toggle_display('items_section', is_saved);
	},

	get_items(frm) {
		fetch_items_from_sales_order(frm);
	}
});

function fetch_items_from_sales_order(frm) {
	if (!frm.doc.sales_order) {
		frappe.msgprint(__('Please select a Sales Order first.'));
		return;
	}

	frappe.call({
		method: 'jain_machine_tools.jain_machine_tools.doctype.delivery_planning_schedule.delivery_planning_schedule.get_items_from_sales_order',
		args: {
			sales_order: frm.doc.sales_order
		},
		callback(r) {
			if (!r.message) {
				return;
			}

			apply_sales_order_data(frm, r.message);
		}
	});
}

function apply_sales_order_data(frm, data) {
	frm.set_value('company', data.company);
	frm.set_value('customer', data.customer);
	if (data.schedule_date) {
		frm.set_value('schedule_date', data.schedule_date);
	}

	frm.clear_table('items');
	(data.items || []).forEach((row) => {
		const child = frm.add_child('items');
		child.sales_order_item = row.sales_order_item;
		child.planned_qty = row.planned_qty;
		child.item_code = row.item_code;
		child.delivery_date = row.delivery_date;
		child.qty = row.qty;
		child.uom = row.uom;
		child.description = row.description;
	});

	frm.refresh_field('items');
	frm.refresh_field('company');
	frm.refresh_field('customer');
}
