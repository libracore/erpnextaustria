/* Copyright (c) 2024, libracore (https://www.libracore.com) and contributors */

frappe.ui.form.on('Fiscal Year', {
    refresh(frm) {
        frm.add_custom_button(__("ACL Export"), function() {
            frappe.prompt(
                [
                    {
                        'fieldname': 'company', 
                        'fieldtype': 'Link', 
                        'label': __('Company'), 
                        'options': "Company", 
                        'default': frappe.defaults.get_user_default("company"),
                        'reqd': 1
                    }  
                ],
                function(values){
                    frappe.call({
                        "method": "erpnextaustria.erpnextaustria.financial_export.async_create_financial_export",
                        "args": {
                            "company": values.company,
                            "fiscal_year": frm.doc.name
                        },
                        "callback": function(response) {
                            frappe.show_alert(response.message);
                        }
                    });
                },
                __("Company"),
                __("OK")
            );
        });
	}
});