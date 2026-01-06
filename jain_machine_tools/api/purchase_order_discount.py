import frappe
from frappe.utils import flt

def validate_items(doc, method):
    for item in doc.items:
        # Data fetching
        price_list_rate = flt(item.price_list_rate)
        
        # Custom Fields
        is_non_standard = item.custom_is_non_standard
        ns_percent = flt(item.custom_non_standard_percentage)
        discount_percent = flt(item.custom_discount_percent)
        extra_ns_amt = flt(item.custom_extra_non_standard_amount)
        handling_percent = flt(item.custom_handling_percentage)

        # Variables
        discount_price = 0.0
        absolute_ns_price = 0.0
        final_rate = 0.0

        if is_non_standard:
            # === NON-STANDARD ===
            val_after_ns_percent = price_list_rate + (price_list_rate * (ns_percent / 100.0))
            
            discount_amount = val_after_ns_percent * (discount_percent / 100.0)
            discount_price = val_after_ns_percent - discount_amount
            
            absolute_ns_price = discount_price + extra_ns_amt
            
            handling_amount = absolute_ns_price * (handling_percent / 100.0)
            final_rate = absolute_ns_price + handling_amount
            
        else:
            # === STANDARD ===
            discount_amount = price_list_rate * (discount_percent / 100.0)
            discount_price = price_list_rate - discount_amount
            
            handling_amount = discount_price * (handling_percent / 100.0)
            final_rate = discount_price + handling_amount
            
            absolute_ns_price = 0.0

        # === UPDATE VALUES ===
        item.custom_discount_price = discount_price
        item.custom_absolute_ns_price = absolute_ns_price
        item.rate = final_rate