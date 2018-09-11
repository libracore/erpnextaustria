// Copyright (c) 2017-2018, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Summary Message"] = {
	"filters": [
        {
            "fieldname":"month",
            "label": __("Month"),
            "fieldtype": "Int",
            "reqd": 1,
            "default": new Date().getMonth()
        },
        {
            "fieldname":"year",
            "label": __("Year"),
            "fieldtype": "Int",
            "reqd": 1,
            "default": new Date().getFullYear()
        }
	]
}
