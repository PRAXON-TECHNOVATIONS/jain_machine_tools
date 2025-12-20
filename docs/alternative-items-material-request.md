# Alternative Items in Material Request - Implementation Guide

## Overview
This document outlines all the changes required to support alternative item selection in Material Request that flows through to Work Orders and Subcontracting Orders.

**Scenario:** User creates Material Request with BOM items A, C, D, but selects alternative B instead of A. When Work Order or Subcontracting Order is created, it should use B, C, D instead of A, C, D.

**Current Limitation:** ERPNext currently fetches materials directly from BOM during Work Order/Subcontracting Order creation, ignoring any alternative selections made in Material Request.

---

## 1. Database Schema Changes

### A. Material Request Item DocType
Add three new custom fields:

```python
{
    "fieldname": "alternative_item",
    "label": "Alternative Item",
    "fieldtype": "Link",
    "options": "Item",
    "insert_after": "item_code",
    "read_only": 1,
    "description": "Selected alternative item for BOM materials"
},
{
    "fieldname": "original_item",
    "label": "Original Item",
    "fieldtype": "Link",
    "options": "Item",
    "insert_after": "alternative_item",
    "read_only": 1,
    "hidden": 1,
    "description": "Original BOM item that was replaced"
},
{
    "fieldname": "has_alternative",
    "label": "Has Alternative",
    "fieldtype": "Check",
    "insert_after": "original_item",
    "read_only": 1,
    "description": "Indicates if alternative item is being used"
}
```

### B. Purchase Order Item DocType
Add the same three fields to support Subcontracting flow through Purchase Order.

---

## 2. Material Request Changes

### A. Python File: `material_request.py`
**Location:** `/apps/erpnext/erpnext/stock/doctype/material_request/material_request.py`

#### Change 1: Modify `raise_work_orders()` method (Line 767-829)

**Purpose:** Collect alternative item mappings from Material Request and pass them to Work Order creation.

```python
@frappe.whitelist()
def raise_work_orders(material_request):
    mr = frappe.get_doc("Material Request", material_request)
    work_orders = []

    # Collect alternative item mappings from MR
    alternative_items_map = {}
    for item in mr.items:
        if item.has_alternative and item.alternative_item and item.original_item:
            alternative_items_map[item.name] = {
                "original_item": item.original_item,
                "alternative_item": item.alternative_item,
                "item_code": item.item_code
            }

    for d in mr.items:
        if d.stock_qty - d.ordered_qty > 0:
            if frappe.db.exists("BOM", {"item": d.item_code, "is_active": 1, "is_default": 1}):
                wo_order = frappe.new_doc("Work Order")
                wo_order.update({
                    "production_item": d.item_code,
                    "qty": d.stock_qty - d.ordered_qty,
                    "company": mr.company,
                    "material_request": mr.name,
                    "material_request_item": d.name,
                    "bom_no": get_item_details(d.item_code).get("bom_no"),
                    "stock_uom": d.stock_uom,
                    "warehouse": d.warehouse,
                })

                # Pass alternative items mapping to Work Order
                if d.name in alternative_items_map:
                    wo_order.flags.mr_alternative_items = {d.name: alternative_items_map[d.name]}

                wo_order.get_items_and_operations_from_bom()
                wo_order.insert()
                work_orders.append(wo_order.name)

    return work_orders
```

#### Change 2: Modify `make_purchase_order()` function (Line 434)

**Purpose:** Transfer alternative item selections from Material Request to Purchase Order (for Subcontracting flow).

```python
@frappe.whitelist()
def make_purchase_order(source_name, target_doc=None):
    def postprocess(source, target_doc):
        if target_doc.get("__islocal"):
            target_doc.supplier = source.supplier
            target_doc.apply_discount_on = ""
            target_doc.additional_discount_percentage = 0.0
            target_doc.discount_amount = 0.0
            target_doc.inter_company_order_reference = ""

        set_missing_values(source, target_doc)

        # Transfer alternative item selections to PO
        for mr_item in source.items:
            if mr_item.has_alternative and mr_item.alternative_item:
                for po_item in target_doc.items:
                    if po_item.material_request_item == mr_item.name:
                        po_item.alternative_item = mr_item.alternative_item
                        po_item.original_item = mr_item.original_item
                        po_item.has_alternative = 1

    # ... rest of mapping code remains same ...
```

### B. JavaScript File: `material_request.js`
**Location:** `/apps/erpnext/erpnext/stock/doctype/material_request/material_request.js`

#### Change 1: Add "Select Alternative Items" button

```javascript
// Add after the "Manufacture" button setup (around line 186)
if (doc.material_request_type === "Manufacture" && doc.docstatus === 1) {
    frm.add_custom_button(__("Select Alternative Items"), function () {
        me.select_alternative_items(frm);
    }, __("Tools"));
}
```

#### Change 2: Add alternative item selection methods

```javascript
select_alternative_items: function(frm) {
    let items_with_bom = [];

    // Get items that have BOM with materials allowing alternatives
    frm.doc.items.forEach((item) => {
        if (item.item_code) {
            frappe.db.get_value("Item", item.item_code, "default_bom")
                .then(r => {
                    if (r.message && r.message.default_bom) {
                        frappe.db.get_list("BOM Item", {
                            filters: {
                                parent: r.message.default_bom,
                                allow_alternative_item: 1
                            },
                            fields: ["item_code", "item_name", "qty", "stock_uom", "allow_alternative_item"]
                        }).then(bom_items => {
                            if (bom_items.length > 0) {
                                items_with_bom.push({
                                    mr_item: item,
                                    bom_no: r.message.default_bom,
                                    bom_items: bom_items
                                });
                            }
                        });
                    }
                });
        }
    });

    // Show dialog after data is loaded
    setTimeout(() => {
        me.show_alternative_items_dialog(frm, items_with_bom);
    }, 1500);
},

show_alternative_items_dialog: function(frm, items_data) {
    let me = this;

    if (!items_data || items_data.length === 0) {
        frappe.msgprint(__("No items with alternative materials found in BOM"));
        return;
    }

    let dialog = new frappe.ui.Dialog({
        title: __("Select Alternative Items for BOM Materials"),
        size: "large",
        fields: [],
        primary_action_label: __("Update Alternatives"),
        primary_action: function(values) {
            me.update_mr_alternatives(frm, values, items_data);
            dialog.hide();
        }
    });

    // Build dialog fields for each BOM item that allows alternatives
    items_data.forEach((data, idx) => {
        dialog.fields_dict = dialog.fields_dict || {};

        dialog.fields.push({
            fieldtype: "Section Break",
            label: __("Finished Good: {0}", [data.mr_item.item_code])
        });

        data.bom_items.forEach((bom_item, bom_idx) => {
            dialog.fields.push({
                fieldtype: "Link",
                fieldname: `alternative_${idx}_${bom_idx}`,
                label: __("Alternative for {0}", [bom_item.item_code]),
                options: "Item",
                get_query: function() {
                    return {
                        filters: {
                            name: ["in", me.get_alternative_items(bom_item.item_code)]
                        }
                    };
                },
                description: __("Original: {0} ({1} {2})", [bom_item.item_code, bom_item.qty, bom_item.stock_uom])
            });
        });
    });

    dialog.show();
    dialog.$wrapper.find(".modal-dialog").css("width", "800px");
},

get_alternative_items: function(item_code) {
    let alternatives = [item_code]; // Include original item

    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Item Alternative",
            filters: {
                item_code: item_code
            },
            fields: ["alternative_item_code"],
            async: false
        },
        callback: function(r) {
            if (r.message) {
                r.message.forEach(alt => {
                    alternatives.push(alt.alternative_item_code);
                });
            }
        }
    });

    return alternatives;
},

update_mr_alternatives: function(frm, values, items_data) {
    let updates = [];

    items_data.forEach((data, idx) => {
        data.bom_items.forEach((bom_item, bom_idx) => {
            let field_name = `alternative_${idx}_${bom_idx}`;
            let selected_alternative = values[field_name];

            if (selected_alternative && selected_alternative !== bom_item.item_code) {
                updates.push({
                    mr_item_name: data.mr_item.name,
                    original_item: bom_item.item_code,
                    alternative_item: selected_alternative
                });
            }
        });
    });

    if (updates.length > 0) {
        frappe.call({
            method: "jain_machine_tools.utils.alternative_items.update_material_request_alternatives",
            args: {
                material_request: frm.doc.name,
                updates: updates
            },
            callback: function(r) {
                if (!r.exc) {
                    frappe.msgprint(__("Alternative items updated successfully"));
                    frm.reload_doc();
                }
            }
        });
    } else {
        frappe.msgprint(__("No alternative items selected"));
    }
}
```

---

## 3. Work Order Changes

### A. Python File: `work_order.py`
**Location:** `/apps/erpnext/erpnext/manufacturing/doctype/work_order/work_order.py`

#### Change 1: Modify `set_required_items()` method (Lines 1141-1183)

**Purpose:** Apply alternative items from Material Request to Work Order's required_items table.

```python
def set_required_items(self, reset_only_qty=False):
    """Set required items from BOM, with support for Material Request alternative items"""
    if self.bom_no and self.qty:
        item_dict = get_bom_items_as_dict(
            self.bom_no,
            self.company,
            qty=self.qty,
            fetch_exploded=self.use_multi_level_bom,
            fetch_qty_in_stock_uom=True,
        )

        # Check if we have alternative items from Material Request
        alternative_items_map = None

        # Method 1: Check if passed via flags (from raise_work_orders)
        if hasattr(self, 'flags') and self.flags.get('mr_alternative_items'):
            mr_alternatives = self.flags.mr_alternative_items.get(self.material_request_item)
            if mr_alternatives:
                alternative_items_map = {mr_alternatives['original_item']: mr_alternatives}

        # Method 2: Fetch from Material Request if not in flags
        elif self.material_request and self.material_request_item:
            alternative_items_map = self.get_alternative_items_from_mr()

        # Apply alternative items to BOM items dict
        if alternative_items_map:
            item_dict = self.apply_alternative_items_to_bom(item_dict, alternative_items_map)

        if reset_only_qty:
            for d in self.get("required_items"):
                if item_dict.get(d.item_code):
                    d.required_qty = item_dict.get(d.item_code).get("qty")
        else:
            # Clear existing items
            self.set("required_items", [])

            # Add items from BOM (potentially with alternatives applied)
            operation = frappe.db.get_value("BOM", self.bom_no, "operation", cache=True)
            for item in sorted(item_dict.values(), key=lambda d: d["idx"] or float("inf")):
                self.append("required_items", {
                    "rate": item.rate,
                    "amount": item.rate * item.qty,
                    "operation": item.operation or operation,
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "description": item.description,
                    "allow_alternative_item": item.allow_alternative_item,
                    "required_qty": item.qty,
                    "source_warehouse": item.source_warehouse or item.default_warehouse,
                    "include_item_in_manufacturing": item.include_item_in_manufacturing,
                    "original_item": item.get("original_item"),  # Track if alternative was used
                })

        self.set_available_qty()
```

#### Change 2: Add new method `get_alternative_items_from_mr()`

```python
def get_alternative_items_from_mr(self):
    """Fetch alternative items selected in Material Request"""
    if not self.material_request:
        return None

    mr = frappe.get_doc("Material Request", self.material_request)
    alternatives = {}

    for item in mr.items:
        if item.has_alternative and item.alternative_item and item.original_item:
            alternatives[item.original_item] = {
                "alternative_item": item.alternative_item,
                "original_item": item.original_item
            }

    return alternatives if alternatives else None
```

#### Change 3: Add new method `apply_alternative_items_to_bom()`

```python
def apply_alternative_items_to_bom(self, bom_items_dict, alternative_items_map):
    """Replace BOM items with alternatives from Material Request"""
    updated_dict = {}

    for item_code, item_data in bom_items_dict.items():
        # Check if this item has an alternative selected
        if item_code in alternative_items_map:
            alt_item_code = alternative_items_map[item_code]["alternative_item"]

            # Get alternative item details
            alt_item = frappe.get_doc("Item", alt_item_code)

            # Update item data with alternative
            item_data["original_item"] = item_code
            item_data["item_code"] = alt_item_code
            item_data["item_name"] = alt_item.item_name
            item_data["description"] = alt_item.description
            item_data["stock_uom"] = alt_item.stock_uom

            # Fetch item defaults (warehouse, rate)
            item_defaults = frappe.db.get_value(
                "Item Default",
                {"parent": alt_item_code, "company": self.company},
                ["default_warehouse"],
                as_dict=1
            )
            if item_defaults:
                item_data["default_warehouse"] = item_defaults.default_warehouse

            # Use alternative item code as key
            updated_dict[alt_item_code] = item_data
        else:
            updated_dict[item_code] = item_data

    return updated_dict
```

---

## 4. Subcontracting Order Changes

### A. Python File: `subcontracting_controller.py`
**Location:** `/apps/erpnext/erpnext/controllers/subcontracting_controller.py`

#### Change 1: Enhance `__set_supplied_items()` method (Line 848)

**Purpose:** Check for pre-selected alternatives from Material Request before applying default alternative logic.

```python
def __set_supplied_items(self, row, qty, reset_only_qty=False):
    # Check if this came from a Material Request with alternatives
    alternative_items = self.get_alternative_items_from_source()

    if self.doctype == self.subcontract_data.order_doctype or (
        self.backflush_based_on == "BOM" or self.is_return
    ):
        for bom_item in self._get_materials_from_bom(
            row.item_code, row.bom, row.get("include_exploded_items")
        ):
            qty = flt(bom_item.qty_consumed_per_unit) * flt(row.qty) * row.conversion_factor
            bom_item.main_item_code = row.item_code

            self.__update_reserve_warehouse(bom_item, row)

            # Check if we have pre-selected alternative from MR → PO
            if alternative_items and bom_item.rm_item_code in alternative_items:
                # Get alternative item details
                alt_item = frappe.get_doc("Item", alternative_items[bom_item.rm_item_code]["alternative_item"])

                bom_item.update({
                    "rm_item_code": alt_item.item_code,
                    "item_name": alt_item.item_name,
                    "stock_uom": alt_item.stock_uom,
                    "conversion_factor": 1,
                    "original_item": bom_item.rm_item_code
                })
            else:
                # Use existing alternative item logic (from Stock Entry)
                self.__set_alternative_item(bom_item)

            self.__add_supplied_item(row, bom_item, qty)
    else:
        # ... existing code for other scenarios ...
```

#### Change 2: Add new method `get_alternative_items_from_source()`

```python
def get_alternative_items_from_source(self):
    """Get alternative items if this PO came from Material Request"""
    # For Purchase Order (Subcontracting type)
    if not hasattr(self, 'items') or not self.items:
        return None

    alternatives = {}

    # Check each PO item for alternative item data
    for item in self.items:
        if hasattr(item, 'has_alternative') and item.has_alternative:
            if item.alternative_item and item.original_item:
                alternatives[item.original_item] = {
                    "alternative_item": item.alternative_item,
                    "original_item": item.original_item
                }

    return alternatives if alternatives else None
```

---

## 5. Utility Functions

### Create new file: `alternative_items.py`
**Location:** `/apps/jain_machine_tools/jain_machine_tools/utils/alternative_items.py`

```python
import frappe
from frappe import _

@frappe.whitelist()
def update_material_request_alternatives(material_request, updates):
    """
    Update Material Request items with alternative item selections

    Args:
        material_request: Material Request name
        updates: List of dicts with mr_item_name, original_item, alternative_item
    """
    if isinstance(updates, str):
        import json
        updates = json.loads(updates)

    mr = frappe.get_doc("Material Request", material_request)

    for update in updates:
        for item in mr.items:
            if item.name == update['mr_item_name']:
                # Validate alternative item
                validate_alternative_item(update['original_item'], update['alternative_item'])

                # Update item fields
                item.original_item = update['original_item']
                item.alternative_item = update['alternative_item']
                item.has_alternative = 1
                break

    mr.save()
    frappe.db.commit()

    return {"status": "success", "message": _("Alternative items updated")}


def get_alternative_items_for_bom(bom_no):
    """Get all items from BOM that allow alternatives"""
    return frappe.db.sql("""
        SELECT
            item_code,
            item_name,
            qty,
            stock_uom,
            allow_alternative_item
        FROM `tabBOM Item`
        WHERE parent = %s AND allow_alternative_item = 1
        ORDER BY idx
    """, bom_no, as_dict=1)


def validate_alternative_item(original_item, alternative_item):
    """Validate that alternative item is compatible with original"""
    # Check if alternative is registered in Item Alternative doctype
    alternative_exists = frappe.db.exists("Item Alternative", {
        "item_code": original_item,
        "alternative_item_code": alternative_item
    })

    # Also check reverse direction (bidirectional alternatives)
    if not alternative_exists:
        alternative_exists = frappe.db.exists("Item Alternative", {
            "item_code": alternative_item,
            "alternative_item_code": original_item
        })

    if not alternative_exists:
        frappe.throw(
            _("{0} is not a registered alternative for {1}. Please add it in Item Alternative doctype first.").format(
                frappe.bold(alternative_item),
                frappe.bold(original_item)
            )
        )

    # Fetch both items
    original = frappe.get_doc("Item", original_item)
    alternative = frappe.get_doc("Item", alternative_item)

    # Validate stock item property
    if original.is_stock_item != alternative.is_stock_item:
        frappe.throw(_("Alternative item must match 'Is Stock Item' property"))

    # Validate serial/batch compatibility
    if original.has_serial_no != alternative.has_serial_no:
        frappe.throw(_("Alternative item must match 'Has Serial No' property"))

    if original.has_batch_no != alternative.has_batch_no:
        frappe.throw(_("Alternative item must match 'Has Batch No' property"))

    return True


def get_registered_alternatives(item_code):
    """Get all registered alternative items for a given item"""
    alternatives = []

    # Get alternatives where this item is primary
    alt_list = frappe.db.sql("""
        SELECT alternative_item_code, alternative_item_name
        FROM `tabItem Alternative`
        WHERE item_code = %s
    """, item_code, as_dict=1)

    alternatives.extend([alt.alternative_item_code for alt in alt_list])

    # Get alternatives where this item is the alternative (bidirectional)
    alt_list_reverse = frappe.db.sql("""
        SELECT item_code as alternative_item_code
        FROM `tabItem Alternative`
        WHERE alternative_item_code = %s
    """, item_code, as_dict=1)

    alternatives.extend([alt.alternative_item_code for alt in alt_list_reverse])

    return list(set(alternatives))  # Remove duplicates


def replace_bom_items_with_alternatives(bom_items_dict, alternatives_map):
    """
    Replace items in BOM dict with alternatives

    Args:
        bom_items_dict: Dict from get_bom_items_as_dict()
        alternatives_map: Dict of {original_item: {"alternative_item": alt_code, "original_item": orig_code}}

    Returns:
        Updated bom_items_dict with alternatives applied
    """
    updated_dict = {}

    for original_item, alt_data in alternatives_map.items():
        if original_item in bom_items_dict:
            bom_item = bom_items_dict[original_item]
            alt_item_code = alt_data["alternative_item"]

            # Fetch alternative item details
            alt_item = frappe.get_doc("Item", alt_item_code)

            # Update the dict entry
            bom_item["original_item"] = original_item
            bom_item["item_code"] = alt_item_code
            bom_item["item_name"] = alt_item.item_name
            bom_item["description"] = alt_item.description
            bom_item["stock_uom"] = alt_item.stock_uom

            # Add with new key (alternative item code)
            updated_dict[alt_item_code] = bom_item
        else:
            # Item not in BOM, skip
            pass

    # Add remaining items that weren't replaced
    for item_code, item_data in bom_items_dict.items():
        if item_code not in alternatives_map:
            updated_dict[item_code] = item_data

    return updated_dict
```

---

## 6. Custom Fields Creation Script

### Create patch file: `add_alternative_item_fields_to_mr.py`
**Location:** `/apps/jain_machine_tools/jain_machine_tools/patches/add_alternative_item_fields_to_mr.py`

```python
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """
    Add custom fields for alternative item handling to:
    1. Material Request Item
    2. Purchase Order Item
    """

    custom_fields = {
        "Material Request Item": [
            {
                "fieldname": "alternative_item",
                "label": "Alternative Item",
                "fieldtype": "Link",
                "options": "Item",
                "insert_after": "item_code",
                "read_only": 1,
                "description": "Selected alternative item for BOM materials",
                "translatable": 0
            },
            {
                "fieldname": "original_item",
                "label": "Original Item",
                "fieldtype": "Link",
                "options": "Item",
                "insert_after": "alternative_item",
                "read_only": 1,
                "hidden": 1,
                "description": "Original BOM item that was replaced",
                "translatable": 0
            },
            {
                "fieldname": "has_alternative",
                "label": "Has Alternative",
                "fieldtype": "Check",
                "insert_after": "original_item",
                "read_only": 1,
                "default": 0,
                "description": "Indicates if alternative item is being used"
            }
        ],
        "Purchase Order Item": [
            {
                "fieldname": "alternative_item",
                "label": "Alternative Item",
                "fieldtype": "Link",
                "options": "Item",
                "insert_after": "item_code",
                "read_only": 1,
                "description": "Alternative item from Material Request",
                "translatable": 0
            },
            {
                "fieldname": "original_item",
                "label": "Original Item",
                "fieldtype": "Link",
                "options": "Item",
                "insert_after": "alternative_item",
                "read_only": 1,
                "hidden": 1,
                "description": "Original item from Material Request",
                "translatable": 0
            },
            {
                "fieldname": "has_alternative",
                "label": "Has Alternative",
                "fieldtype": "Check",
                "insert_after": "original_item",
                "read_only": 1,
                "default": 0,
                "description": "Indicates if alternative item is being used"
            }
        ]
    }

    create_custom_fields(custom_fields, update=True)
    frappe.db.commit()

    print("Successfully added alternative item fields to Material Request Item and Purchase Order Item")
```

### Add to patches.txt
**Location:** `/apps/jain_machine_tools/jain_machine_tools/patches.txt`

```
[post_model_sync]
jain_machine_tools.patches.add_item_custom_fields
jain_machine_tools.patches.add_party_specific_item_fields
jain_machine_tools.patches.add_alternative_item_fields_to_mr
```

---

## 7. Summary of All Files to Modify/Create

| # | Action | File Path | Description |
|---|--------|-----------|-------------|
| 1 | **Create** | `jain_machine_tools/utils/alternative_items.py` | Utility functions for alternative item handling |
| 2 | **Create** | `jain_machine_tools/patches/add_alternative_item_fields_to_mr.py` | Custom fields creation patch |
| 3 | **Modify** | `jain_machine_tools/patches.txt` | Add new patch entry |
| 4 | **Override** | `jain_machine_tools/overrides/material_request.py` | Override `raise_work_orders()` and `make_purchase_order()` |
| 5 | **Create** | `jain_machine_tools/public/js/material_request.js` | Client-side alternative item selection UI |
| 6 | **Override** | `jain_machine_tools/overrides/work_order.py` | Override `set_required_items()` with alternative item support |
| 7 | **Override** | `jain_machine_tools/overrides/subcontracting_controller.py` | Override `__set_supplied_items()` |

---

## 8. Implementation Approach

Since we need to modify core ERPNext files, we'll use **method overriding** via hooks instead of directly editing ERPNext files.

### A. Hook Configuration
**Location:** `/apps/jain_machine_tools/jain_machine_tools/hooks.py`

```python
# Document Events
doc_events = {
    "Work Order": {
        "validate": "jain_machine_tools.overrides.work_order.apply_mr_alternatives"
    },
    "Subcontracting Order": {
        "validate": "jain_machine_tools.overrides.subcontracting_order.apply_mr_alternatives"
    }
}

# Override Whitelisted Methods
override_whitelisted_methods = {
    "erpnext.stock.doctype.material_request.material_request.raise_work_orders":
        "jain_machine_tools.overrides.material_request.raise_work_orders",
    "erpnext.stock.doctype.material_request.material_request.make_purchase_order":
        "jain_machine_tools.overrides.material_request.make_purchase_order"
}

# Include JS/CSS files
app_include_js = [
    "/assets/jain_machine_tools/js/material_request.js"
]
```

---

## 9. Testing Checklist

After implementation, test these scenarios:

### Basic Flow
- [ ] Create Material Request (Manufacture type) with item that has BOM
- [ ] Click "Select Alternative Items" button
- [ ] Select alternative for one or more BOM materials
- [ ] Save Material Request and verify alternative fields are populated
- [ ] Click "Manufacture" → Create Work Order
- [ ] Verify Work Order's `required_items` shows alternative items
- [ ] Create Stock Entry from Work Order
- [ ] Verify Stock Entry items show alternative items

### Subcontracting Flow
- [ ] Create Material Request (Purchase type, Subcontracting)
- [ ] Select alternative items
- [ ] Create Purchase Order (Subcontracting)
- [ ] Verify PO has alternative fields populated
- [ ] Create Subcontracting Order from PO
- [ ] Verify `supplied_items` shows alternative items

### Edge Cases
- [ ] Multiple alternatives for different materials in same BOM
- [ ] Partial alternative selection (some materials with alternatives, some without)
- [ ] Work Order created without Material Request (should use BOM items)
- [ ] Material Request without alternatives selected
- [ ] Invalid alternative item (not registered in Item Alternative)
- [ ] Alternative item with incompatible properties

### Validation
- [ ] Alternative item not in Item Alternative doctype → Should show error
- [ ] Alternative with different stock item property → Should show error
- [ ] Alternative with different serial/batch property → Should show error
- [ ] Verify costing is correct with alternative items

---

## 10. Key Implementation Notes

### Important Considerations

1. **Stock Entry Behavior**: Stock Entry reads from Work Order's `required_items` table (via `get_pro_order_required_items()`), NOT from BOM directly. This means our changes to Work Order's `required_items` will automatically flow to Stock Entry.

2. **Method Overriding**: We use `override_whitelisted_methods` in hooks.py to intercept the `raise_work_orders()` and `make_purchase_order()` calls without modifying core ERPNext files.

3. **Alternative Item Validation**: Always validate using `Item Alternative` doctype before allowing selection. This ensures compatibility.

4. **Backward Compatibility**: Work Orders created without Material Request should continue working normally with BOM items.

5. **Performance**: The dialog for selecting alternatives makes multiple DB calls. Consider caching or optimizing for large BOMs.

---

## 11. Future Enhancements

1. **Bulk Alternative Selection**: Allow setting alternatives at Item Group level
2. **Auto-selection Based on Stock**: Automatically select alternative with highest stock
3. **Price Comparison**: Show price difference when selecting alternatives
4. **History Tracking**: Track which alternatives were used in past orders
5. **Mobile Support**: Optimize UI for mobile devices

---

## 12. Support and Maintenance

For issues or questions regarding this implementation, refer to:
- ERPNext Documentation: https://docs.erpnext.com
- Frappe Framework Docs: https://frappeframework.com/docs
- Item Alternative feature: https://docs.erpnext.com/docs/user/manual/en/stock/item-alternative

**Document Version:** 1.0
**Last Updated:** December 18, 2025
**Author:** Ujjwal Aggrawal 
