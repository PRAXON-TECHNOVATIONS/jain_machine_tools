// Copyright (c) 2025, Praxon Technovation and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Non Standard Item Configurator", {
//     base_item(frm) {
//         frm.set_query("select_base_price", () => {
//             if (!frm.doc.base_item) {
//                 return {};
//             }
//             return {
//                 filters: {
//                     item_code: frm.doc.base_item,
//                 }
//             };
//         });
//     },

//     refresh(frm) {
//         if (frm.doc.base_item) {
//             frm.trigger("base_item");
//         }
//         if (frm.is_new()) {
//             frm.toggle_display("create_item", false);
//         } else {
//             frm.toggle_display("create_item", true);
//         }
//     },

//     create_item(frm) {
//         frappe.call({
//             method: "create_item_and_price",
//             doc: frm.doc,
//             callback: function () {
//                 frm.reload_doc();
//             }
//         });
//     }
// });


// Copyright (c) 2025, Praxon Technovation and contributors
// For license information, please see license.txt

frappe.ui.form.on("Non Standard Item Configurator", {
    setup(frm) {
        // -----------------------------------------
        // MASTER LISTS (Yahan se copy paste karke niche assign karna aasan hoga)
        // -----------------------------------------
        
        // Frequency: 50 Hz (Standard), 60 Hz
        
        // Voltage: Standard (415V), 220V, 380V, 460V, 690V, Dual Voltage, Triple Voltage, 
        // Other Voltage (< 500V), Other Voltage (> 500V), 
        // Inverter Duty Winding (<= 500V), Inverter Duty Winding (> 500V)
        
        // Mounting: B3 (Foot Mounted) (Standard), B5 (Flange Mounted), B14 (Face Mounted), 
        // B35 (Foot + Flange), B34 (Foot + Face), V1 (Vertical Shaft Down)
        
        // Paint: Standard Paint, Epoxy Paint, PU Paint (Polyurethane), Epoxy Gel Coat, 
        // Zinc Silicate, C3 / C4 / C5 High Grade, Primer Only (Red Oxide)
    },

    refresh(frm) {
        // 1. Button Hiding Logic
        if (frm.is_new() || frm.is_dirty()) {
            frm.toggle_display("create_item", false);
        } else {
            frm.toggle_display("create_item", true);
        }

        // 2. Base Item Logic
        if (frm.doc.base_item) {
            frm.trigger("base_item");
        }

        // 3. Filter Options based on Manufacturer
        frm.trigger("set_dynamic_options");
    },

    manufacturer(frm) {
        // Jab Manufacturer change ho, tab bhi options filter karo
        frm.trigger("set_dynamic_options");
    },

    base_item(frm) {
        frm.set_query("select_base_price", () => {
            if (!frm.doc.base_item) {
                return {};
            }
            return {
                filters: {
                    item_code: frm.doc.base_item,
                }
            };
        });
        
        // Auto-fetch Manufacturer logic (Jo tumne pehle lagaya tha, uske baad filter trigger karo)
        if (frm.doc.base_item) {
             // Yahan tumhara fetch logic aayega agar client script se kar rahe ho
             // Uske turant baad:
             frm.trigger("set_dynamic_options");
        }
    },

    create_item(frm) {
        if (frm.is_dirty()) {
            frappe.msgprint("Please Save the form before creating the item.");
            return;
        }
        frappe.call({
            method: "create_item_and_price",
            doc: frm.doc,
            callback: function () {
                frm.reload_doc();
            }
        });
    },// -----------------------------------------
    // UPDATED FILTERING LOGIC
    // -----------------------------------------
    set_dynamic_options(frm) {
        let make = frm.doc.manufacturer;

        // Arrays to hold the allowed options
        let allowed_paints = [];
        let allowed_mountings = [];
        let allowed_voltages = [];
        
        // 1. COMMON LISTS
        let common_mountings = [
            "B3 (Foot Mounted) (Standard)", "B5 (Flange Mounted)", 
            "B14 (Face Mounted)", "B35 (Foot + Flange)", 
            "B34 (Foot + Face)", "V1 (Vertical Shaft Down)"
        ];
        
        // 2. MANUFACTURER SPECIFIC LOGIC

        if (make == "Hindustan Electric Motors") {
            // --- HINDUSTAN ---
            // Paint: No PU, No Zinc, No C3-C5
            allowed_paints = [
                "Standard Paint", 
                "Epoxy Paint", 
                "Epoxy Gel Coat", 
                "C3 / C4 / C5 High Grade" ,
                "Primer Only (Red Oxide)"

            ];
            // Voltage: Has Dual, No Triple
            allowed_voltages = [
                "Standard (415V)", "220V", "380V", "460V", "690V", 
                "Dual Voltage", "Other Voltage (< 500V)", "Other Voltage (> 500V)",
                "Inverter Duty Winding (<= 500V)", "Inverter Duty Winding (> 500V)"
            ]; 
            allowed_mountings = [...common_mountings, "V18 / V19 (Vertical Special)"];

        } else if (make == "CG Power") {
            // --- CG POWER ---
            // Paint: No PU, No Gel Coat, No Primer
            allowed_paints = [
                "Standard Paint", 
                "Epoxy Paint", 
                "Epoxy Gel Coat", 
                "Zinc Silicate", 
                "C3 / C4 / C5 High Grade"
            ];
            // Voltage: Has Dual AND Triple
            allowed_voltages = [
                "Standard (415V)", "220V", "380V", "460V", "690V", 
                "Dual Voltage", "Triple Voltage", 
                "Other Voltage (< 500V)", "Other Voltage (> 500V)",
                "Inverter Duty Winding (<= 500V)", "Inverter Duty Winding (> 500V)"
            ];
            // CG has special vertical mountings
            allowed_mountings = [...common_mountings, "V18 / V19 (Vertical Special)"];

        } else if (make == "Siemens") {
            // --- SIEMENS ---
            // Paint: PU allowed. No Zinc, No Gel Coat
            allowed_paints = [
                "Standard Paint", 
                "Epoxy Paint", 
                "PU Paint (Polyurethane)", 
                "Primer Only (Red Oxide)"
            ];
            // Voltage: REMOVED 'Dual Voltage' and 'Triple Voltage'
            allowed_voltages = [
                "Standard (415V)", "220V", "380V", "460V", "690V", 
                "Other Voltage (< 500V)", "Other Voltage (> 500V)",
                "Inverter Duty Winding (<= 500V)", "Inverter Duty Winding (> 500V)"
            ];
            allowed_mountings = common_mountings;

        } else {
            // Fallback (Show Everything)
            allowed_paints = [
                "Standard Paint", "Epoxy Paint", "PU Paint (Polyurethane)", 
                "Epoxy Gel Coat", "Zinc Silicate", "C3 / C4 / C5 High Grade", 
                "Primer Only (Red Oxide)"
            ];
            allowed_voltages = [
                "Standard (415V)", "220V", "380V", "460V", "690V", 
                "Dual Voltage", "Triple Voltage", "Other Voltage (< 500V)", 
                "Other Voltage (> 500V)", "Inverter Duty Winding (<= 500V)", 
                "Inverter Duty Winding (> 500V)"
            ];
            allowed_mountings = common_mountings;
        }

        // Apply Options to Fields
        frm.set_df_property("paint_type", "options", allowed_paints);
        frm.set_df_property("voltage", "options", allowed_voltages);
        frm.set_df_property("mounting", "options", allowed_mountings);
        
        // Frequency sabke liye same
        frm.set_df_property("frequency", "options", ["50 Hz (Standard)", "60 Hz"]);
    }
});