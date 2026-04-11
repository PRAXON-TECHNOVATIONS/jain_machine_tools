# Copyright (c) 2026, Jain Machine Tools and contributors
# For license information, please see license.txt

import frappe
from frappe.model.naming import make_autoname


def get_fy_short(date=None):
	"""
	Returns fiscal year in short format like '26-27' from fiscal year '2025-2026'.
	Uses the document date (or today) to look up the active fiscal year.
	"""
	from erpnext.accounts.utils import get_fiscal_year
	from frappe.utils import nowdate

	d = date or nowdate()
	try:
		fy = get_fiscal_year(d, as_dict=True)
		# fy.name is like '2025-2026' → extract last 2 digits of each part
		parts = fy.name.split("-")
		return f"{parts[0][-2:]}-{parts[1][-2:]}"
	except Exception:
		# Fallback: derive from date year (e.g. Apr 2026 → 26-27)
		from frappe.utils import getdate
		year = getdate(d).year
		# Indian FY: Apr–Mar, so if month >= 4 it's FY year/year+1
		month = getdate(d).month
		if month >= 4:
			return f"{str(year)[-2:]}-{str(year + 1)[-2:]}"
		else:
			return f"{str(year - 1)[-2:]}-{str(year)[-2:]}"


def _doc_date(doc):
	"""Pick the most appropriate date field from the document."""
	return (
		doc.get("posting_date")
		or doc.get("transaction_date")
		or doc.get("schedule_date")
		or doc.get("due_date")
	)


def _autoname(doc, prefix):
	"""
	Set doc.name using the format  PREFIX-YY-YY/00001
	e.g. MR-26-27/00001, SO-26-27/00001
	The series counter is keyed per fiscal year automatically.
	"""
	fy_short = get_fy_short(_doc_date(doc))
	# Frappe requires at least one dot in the series format string.
	# Format: PREFIX-YY-YY/.##### → splits on '.' → "PREFIX-YY-YY/" + "00001"
	# Series key stored in tabSeries: "PREFIX-YY-YY/."
	series_key = f"{prefix}-{fy_short}/.#####"
	doc.name = make_autoname(series_key, doc=doc)
	# Keep naming_series in sync so print formats / reports can read it
	if hasattr(doc, "naming_series"):
		doc.naming_series = series_key


# ---------------------------------------------------------------------------
# Override classes — one per doctype.
# Each class inherits from the original ERPNext class so that ALL existing
# behaviour (validate, submit hooks, etc.) is preserved. We only add autoname.
# ---------------------------------------------------------------------------

from erpnext.stock.doctype.material_request.material_request import MaterialRequest


class JMTMaterialRequest(MaterialRequest):
	def autoname(self):
		_autoname(self, "MR")


from erpnext.buying.doctype.request_for_quotation.request_for_quotation import RequestforQuotation


class JMTRequestForQuotation(RequestforQuotation):
	def autoname(self):
		_autoname(self, "RFQ")


from erpnext.buying.doctype.supplier_quotation.supplier_quotation import SupplierQuotation


class JMTSupplierQuotation(SupplierQuotation):
	def autoname(self):
		_autoname(self, "SQ")


from erpnext.buying.doctype.purchase_order.purchase_order import PurchaseOrder


class JMTPurchaseOrder(PurchaseOrder):
	def autoname(self):
		_autoname(self, "PO")


from erpnext.crm.doctype.lead.lead import Lead


class JMTLead(Lead):
	def autoname(self):
		_autoname(self, "LD")


from erpnext.crm.doctype.opportunity.opportunity import Opportunity


class JMTOpportunity(Opportunity):
	def autoname(self):
		_autoname(self, "OP")


from erpnext.selling.doctype.quotation.quotation import Quotation


class JMTQuotation(Quotation):
	def autoname(self):
		_autoname(self, "QN")


from erpnext.selling.doctype.sales_order.sales_order import SalesOrder


class JMTSalesOrder(SalesOrder):
	def autoname(self):
		_autoname(self, "SO")


from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice


class JMTSalesInvoice(SalesInvoice):
	def autoname(self):
		# Credit Note (return against Sales Invoice) gets CN prefix
		prefix = "CN" if self.get("is_return") else "IN"
		_autoname(self, prefix)


from erpnext.stock.doctype.delivery_note.delivery_note import DeliveryNote


class JMTDeliveryNote(DeliveryNote):
	def autoname(self):
		_autoname(self, "DL")


from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry


class JMTStockEntry(StockEntry):
	def autoname(self):
		_autoname(self, "SE")


from erpnext.stock.doctype.purchase_receipt.purchase_receipt import PurchaseReceipt


class JMTPurchaseReceipt(PurchaseReceipt):
	def autoname(self):
		_autoname(self, "PR")


from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice


class JMTPurchaseInvoice(PurchaseInvoice):
	def autoname(self):
		# Debit Note (return against Purchase Invoice) gets DN prefix
		prefix = "DN" if self.get("is_return") else "PINV"
		_autoname(self, prefix)
