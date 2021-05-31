// Copyright (c) 2021, libracore and Contributors
// License: GNU General Public License v3. See license.txt

frappe.query_reports["OP Debitoren"] = {
    "filters": [
        {
            "fieldname":"company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "reqd": 1,
            "default": frappe.defaults.get_user_default("Company")
        },
        {
            "fieldname":"ageing_based_on",
            "label": __("Ageing Based On"),
            "fieldtype": "Select",
            "options": 'Posting Date\nDue Date',
            "default": "Posting Date"
        },
        {
            "fieldname":"report_date",
            "label": __("As on Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today()
        },
        {
            "fieldname":"range1",
            "label": __("Ageing Range 1"),
            "fieldtype": "Int",
            "default": "30",
            "reqd": 1
        },
        {
            "fieldname":"range2",
            "label": __("Ageing Range 2"),
            "fieldtype": "Int",
            "default": "60",
            "reqd": 1
        },
        {
            "fieldname":"range3",
            "label": __("Ageing Range 3"),
            "fieldtype": "Int",
            "default": "90",
            "reqd": 1
        },
        {
            "fieldname":"range4",
            "label": __("Ageing Range 4"),
            "fieldtype": "Int",
            "default": "120",
            "reqd": 1
        },
        {
            "fieldname":"finance_book",
            "label": __("Finance Book"),
            "fieldtype": "Link",
            "options": "Finance Book",
            "hidden": 1
        },
        {
            "fieldname":"cost_center",
            "label": __("Cost Center"),
            "fieldtype": "Link",
            "hidden": 1,
            "options": "Cost Center",
            get_query: () => {
                var company = frappe.query_report.get_filter_value('company');
                return {
                    filters: {
                        'company': company
                    }
                }
            }
        },
        {
            "fieldname":"customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer",
            on_change: () => {
                var customer = frappe.query_report.get_filter_value('customer');
                if (customer) {
                    frappe.db.get_value('Customer', customer, ["tax_id", "customer_name", "credit_limit", "payment_terms"], function(value) {
                        frappe.query_report.set_filter_value('tax_id', value["tax_id"]);
                        frappe.query_report.set_filter_value('customer_name', value["customer_name"]);
                        frappe.query_report.set_filter_value('credit_limit', value["credit_limit"]);
                        frappe.query_report.set_filter_value('payment_terms', value["payment_terms"]);
                    });
                } else {
                    frappe.query_report.set_filter_value('tax_id', "");
                    frappe.query_report.set_filter_value('customer_name', "");
                    frappe.query_report.set_filter_value('credit_limit', "");
                    frappe.query_report.set_filter_value('payment_terms', "");
                }
            }
        },
        {
            "fieldname":"customer_group",
            "label": __("Customer Group"),
            "fieldtype": "Link",
            "options": "Customer Group"
        },
        {
            "fieldname":"payment_terms_template",
            "label": __("Payment Terms Template"),
            "fieldtype": "Link",
            "options": "Payment Terms Template",
            "hidden": 1
        },
        {
            "fieldname":"territory",
            "label": __("Territory"),
            "fieldtype": "Link",
            "options": "Territory",
            "hidden": 1
        },
        {
            "fieldname":"sales_partner",
            "label": __("Sales Partner"),
            "fieldtype": "Link",
            "options": "Sales Partner",
            "hidden": 1
        },
        {
            "fieldname":"sales_person",
            "label": __("Sales Person"),
            "fieldtype": "Link",
            "options": "Sales Person",
            "hidden": 1
        },
        {
            "fieldname":"based_on_payment_terms",
            "label": __("Based On Payment Terms"),
            "fieldtype": "Check",
            "hidden": 1
        },
        {
            "fieldname":"show_future_payments",
            "label": __("Show Future Payments"),
            "fieldtype": "Check",
            "hidden": 1
        },
        {
            "fieldname":"show_delivery_notes",
            "label": __("Show Delivery Notes"),
            "fieldtype": "Check",
            "hidden": 1
        },
        {
            "fieldname":"show_sales_person",
            "label": __("Show Sales Person"),
            "fieldtype": "Check",
            "hidden": 1
        },
        {
            "fieldname":"tax_id",
            "label": __("Tax Id"),
            "fieldtype": "Data",
            "hidden": 1
        },
        {
            "fieldname":"customer_name",
            "label": __("Customer Name"),
            "fieldtype": "Data",
            "hidden": 1
        },
        {
            "fieldname":"payment_terms",
            "label": __("Payment Tems"),
            "fieldtype": "Data",
            "hidden": 1
        },
        {
            "fieldname":"credit_limit",
            "label": __("Credit Limit"),
            "fieldtype": "Currency",
            "hidden": 1
        }
    ]
}

erpnext.dimension_filters.forEach((dimension) => {
    frappe.query_reports["OP Debitoren"].filters.splice(9, 0 ,{
        "fieldname": dimension["fieldname"],
        "label": __(dimension["label"]),
        "fieldtype": "Link",
        "options": dimension["document_type"]
    });
});

