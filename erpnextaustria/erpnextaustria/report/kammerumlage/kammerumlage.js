// Copyright (c) 2021, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Kammerumlage"] = {
    "filters": [
        {
            "fieldname":"quarter",
            "label": __("Quarter"),
            "fieldtype": "Select",
            "options": "Q1\nQ2\nQ3\nQ4",
            "default": "Q1",
            "reqd": 1
        },
        {
            "fieldname":"year",
            "label": __("Year"),
            "fieldtype": "Int",
            "default": new Date().getFullYear(),
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
    ],
    onload: function(report) {
        report.page.add_inner_button(__("Download XML"), function() {
            download_xml(report);
        });
    }
}

/* download xml form */
function download_xml(report) {
    // generate summary message xml file
    var filters = report.get_values();
    console.log(filters);
    frappe.call({
        method: 'erpnextaustria.erpnextaustria.report.kammerumlage.kammerumlage.generate_transfer_file',
        args: {
            'filters': filters
        },
        callback: function(r) {
            if (r.message) {
                // prepare the xml file for download
                var today = new Date();
                download("kammerumlage_" + today.getFullYear() + "-" + today.getMonth() + ".xml", r.message.content);
            } 
        }
    });   
}

function download(filename, content) {
    var element = document.createElement('a');
    element.setAttribute('href', 'data:application/octet-stream;charset=utf-8,' + encodeURIComponent(content));
    element.setAttribute('download', filename);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
}
