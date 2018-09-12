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
        method: 'erpnextaustria.erpnextaustria.report.summary_message.summary_message.generate_transfer_file',
        args: {
			'month': filters.month,
			'year': filters.year
		},
        callback: function(r) {
            if (r.message) {
                // prepare the xml file for download
                var today = new Date();
                download("zm_" + today.getFullYear() + "-" + today.getMonth() + ".xml", r.message.content);
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
