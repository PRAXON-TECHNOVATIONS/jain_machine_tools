// Copyright (c) 2025, Praxon Technovation and contributors
// For license information, please see license.txt
// frappe.ui.form.on("Non Standard Item Configurator", {
//     refresh(frm) {
//         if (frm.doc.manufacturer == "CG Power") {
//             frm.trigger("filter_cg_options");
//         }
//     },

//     manufacturer(frm) {
//         frm.trigger("filter_cg_options");
//     },

//     base_item(frm) {
//         // Base item change hone par 'derived_base_type' fetch hone ka wait aur fir filter
//         if (frm.doc.base_item) {
//             setTimeout(() => {
//                 frm.trigger("filter_cg_options");
//             }, 1000); 
//         }
//     },

//     filter_cg_options(frm) {
//         if (frm.doc.manufacturer != "CG Power") return;

//         let base_type = frm.doc.derived_base_type; // Value will be "FLAMEPROOF" or "NON-FLAMEPROOF"

//         // --- THERMISTOR FILTERING ---
//         let all_opts = [
//             "",
//             "NONFLP-3-PTC", 
//             "NONFLP-6-PTC", 
//             "NONFLP-3-PTC-130", 
//             "NONFLP-3-PTC-150",
//             "FLP-3-PTC-130", 
//             "FLP-6-PTC-130", 
//             "FLP-3-PTC-150", 
//             "FLP-6-PTC-150"
//         ];

//         let valid_opts = [];

//         if (base_type == "FLAMEPROOF") {
//             // Show only FLP options
//             valid_opts = all_opts.filter(opt => opt === "" || opt.startsWith("FLP"));
//         } else {
//             // Assume NON-FLAMEPROOF or Empty -> Show NONFLP options
//             valid_opts = all_opts.filter(opt => opt === "" || opt.startsWith("NONFLP"));
//         }

//         frm.set_df_property("thermistor_type", "options", valid_opts);
//     }
// });


// Copyright (c) 2025, Praxon Technovation and contributors
// For license information, please see license.txt
frappe.ui.form.on("Non Standard Item Configurator", {
    create_item(frm) {
        if (frm.is_dirty()) {
            frappe.msgprint("Please Save the form before creating the item.");
            return;
        }

        frappe.call({
            method: "create_item_and_price",
            doc: frm.doc,
            freeze: true,
            freeze_message: "Creating Item & Updating Prices...",
            callback: function(r) {
                if (!r.exc) {
                    frm.reload_doc();
                    frappe.msgprint(`Item: <b>${frm.doc.generated_item_code}</b> updated in Standard Buying & Selling.`);
                }
            }
        });
    },

    refresh(frm) {
        frm.toggle_display("create_item", !frm.is_new());
        // --- EXISTING CG LOGIC ---
        if (frm.doc.manufacturer == "CG Power") {
            frm.trigger("apply_cg_logic");
        }

        // --- NEW CODE: FILTER PRICE LIST BASED ON BASE ITEM ---
        if (frm.doc.base_item) {
            frm.set_query("select_base_price", function() {
                return {
                    filters: {
                        item_code: frm.doc.base_item
                    }
                };
            });
        }
    },

    manufacturer(frm) {
        frm.trigger("apply_cg_logic");
    },

    base_item(frm) {
        if (frm.doc.base_item) {
            // --- EXISTING TIMEOUT ---
            setTimeout(() => {
                frm.trigger("apply_cg_logic");
            }, 1000); 

            // --- NEW CODE: TRIGGER FILTER IMMEDIATELY ---
            frm.set_query("select_base_price", function() {
                return {
                    filters: {
                        item_code: frm.doc.base_item
                    }
                };
            });
        }
    },

    frame_size(frm) {
        // Frame size
        frm.trigger("apply_cg_logic");
    },

    apply_cg_logic(frm) {
        if (frm.doc.manufacturer != "CG Power") return;

        // 1. FILTER THERMISTOR (Based on FLP / Non-FLP)
        let base_type = frm.doc.derived_base_type || ""; 
        let is_flp = base_type.includes("FLAMEPROOF"); // Check for exact keyword

        let all_therm_opts = [
            "",
            "NONFLP-3-PTC", 
            "NONFLP-6-PTC", 
            "NONFLP-3-PTC-130", 
            "NONFLP-3-PTC-150",
            "FLP-3-PTC-130", 
            "FLP-6-PTC-130", 
            "FLP-3-PTC-150", 
            "FLP-6-PTC-150"
        ];

        let valid_therm_opts = [];
        if (is_flp) {
            valid_therm_opts = all_therm_opts.filter(opt => opt === "" || opt.startsWith("FLP"));
        } else {
            valid_therm_opts = all_therm_opts.filter(opt => opt === "" || opt.startsWith("NONFLP"));
        }
        frm.set_df_property("thermistor_type", "options", valid_therm_opts);


        // 2. SHOW/HIDE FIELDS & FILTER OPTIONS (Based on Frame Size)
        let frame = frm.doc.frame_size || 0;

        // --- Rules based on your Python Data ---
        let show_heater = (frame >= 100);
        let show_cooling = (frame >= 160);
        let show_roller = (frame >= 160);
        let show_insulated = (frame >= 160);

        // Apply Visibility
        frm.toggle_display("space_heater_required", show_heater);
        frm.toggle_display("forced_cooling_required", show_cooling);
        frm.toggle_display("roller_bearing_required", show_roller);
        frm.toggle_display("insulated_bearing", show_insulated);

        // --- SPECIAL: Filter Insulated Bearing Options based on Frame ---
        if (show_insulated) {
            let all_ib_opts = [
                "",
                "160IB", "180IB", 
                "200IB", "225IB",
                "2Pole-250IB", "2Pole-280IB", "2Pole-315IB", "2Pole-355IB",
                "4Pole-250IB", "4Pole-280IB", "4Pole-315IB", "4Pole-355IB"
            ];

            let filtered_ib = all_ib_opts.filter(opt => {
                return opt === "" || opt.includes(frame.toString());
            });

            if (filtered_ib.length <= 1) { 
                frm.toggle_display("insulated_bearing", false);
            } else {
                frm.set_df_property("insulated_bearing", "options", filtered_ib);
            }
        }
    }
});