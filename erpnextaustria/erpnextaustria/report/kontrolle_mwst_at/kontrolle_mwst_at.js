// Copyright (c) 2016-2020, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Kontrolle MwSt AT"] = {
	"filters": [
        {
            "fieldname":"from_date",
            "label": __("From date"),
            "fieldtype": "Date",
            "default": new Date().getFullYear() + "-01-01"
        },
        {
            "fieldname":"end_date",
            "label": __("End date"),
            "fieldtype": "Date",
            "default" : frappe.datetime.get_today()
        },
        {
            "fieldname":"code",
            "label": __("Code"),
            "fieldtype": "Select",
            "options": "000\n011\n017\n022\n029\n057\n060\n061\n065\n066\n070\n072\n083",
            "default" : "000",
            "reqd": 1
        },
        {
            "fieldname":"company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default" : frappe.defaults.get_default("Company"),
            "reqd": 1
        }
	]
};
