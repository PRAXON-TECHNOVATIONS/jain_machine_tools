frappe.provide('jain_machine_tools.address_filters');

jain_machine_tools.address_filters = {
	setup_customer_address_filters(frm) {
		this.setup_party_address_filters(frm, {
			party_field: 'customer',
			party_doctype: 'Customer',
			address_fields: ['customer_address', 'shipping_address_name', 'dispatch_address_name']
		});
	},

	setup_supplier_address_filters(frm) {
		this.setup_party_address_filters(frm, {
			party_field: 'supplier',
			party_doctype: 'Supplier',
			address_fields: ['supplier_address', 'shipping_address', 'dispatch_address', 'billing_address']
		});
	},

	setup_party_address_filters(frm, config) {
		const party_field = config.party_field;
		const party_doctype = config.party_doctype;
		const address_fields = config.address_fields || [];

		address_fields.forEach((fieldname) => {
			if (!frm.fields_dict[fieldname]) {
				return;
			}

			frm.set_query(fieldname, () => {
				const party = frm.doc[party_field];

				if (!party) {
					return {
						filters: {
							name: ['in', []]
						}
					};
				}

				return {
					query: 'frappe.contacts.doctype.address.address.address_query',
					filters: {
						link_doctype: party_doctype,
						link_name: party
					}
				};
			});
		});
	},

	setup_party_contact_filters(frm, config) {
		const party_field = config.party_field;
		const party_doctype = config.party_doctype;
		const contact_fields = config.contact_fields || [];

		contact_fields.forEach((fieldname) => {
			if (!frm.fields_dict[fieldname]) {
				return;
			}

			frm.set_query(fieldname, () => {
				const party = frm.doc[party_field];

				if (!party) {
					return {
						filters: {
							name: ['in', []]
						}
					};
				}

				return {
					query: 'frappe.contacts.doctype.contact.contact.contact_query',
					filters: {
						link_doctype: party_doctype,
						link_name: party
					}
				};
			});
		});
	},

	clear_party_addresses(frm, fieldnames) {
		(fieldnames || []).forEach((fieldname) => {
			if (frm.fields_dict[fieldname] && frm.doc[fieldname]) {
				frm.set_value(fieldname, '');
			}
		});
	},

	clear_party_contacts(frm, fieldnames) {
		(fieldnames || []).forEach((fieldname) => {
			if (frm.fields_dict[fieldname] && frm.doc[fieldname]) {
				frm.set_value(fieldname, '');
			}
		});
	},

	async copy_quotation_addresses_to_proforma(frm) {
		if (!frm.doc.quotation || frm.is_new() !== true) {
			return;
		}

		const fields_to_copy = [
			'customer_address',
			'address_display',
			'contact_person',
			'contact_display',
			'contact_mobile',
			'contact_email',
			'shipping_address_name',
			'shipping_address',
			'company_address',
			'company_address_display',
			'company_contact_person',
			'territory',
			'customer_group'
		];

		const needs_fetch = fields_to_copy.some((fieldname) => !frm.doc[fieldname]);
		if (!needs_fetch) {
			return;
		}

		const response = await frappe.db.get_doc('Quotation', frm.doc.quotation);
		if (!response) {
			return;
		}

		const values = {};
		fields_to_copy.forEach((fieldname) => {
			if (response[fieldname] && !frm.doc[fieldname] && frm.fields_dict[fieldname]) {
				values[fieldname] = response[fieldname];
			}
		});

		if (Object.keys(values).length) {
			await frm.set_value(values);
		}
	}
};
