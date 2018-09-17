// Copyright (c) 2018, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Intrastat"] = {
	"filters": [
        {
            "fieldname":"month",
            "label": __("Month"),
            "fieldtype": "Int",
            "reqd": 1,
            "default": (new Date().getMonth() + 1)
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
		report.page.add_inner_button(__("Download CSV"), function() {
			download_csv(report);
		});
	}
}

/* download csv form */
function download_csv(report) {
    // generate intrastat csv file
    var filters = report.get_values();
    console.log(filters);
    frappe.call({
        method: 'erpnextaustria.erpnextaustria.report.intrastat.intrastat.generate_transfer_file',
        args: {
			'month': filters.month,
			'year': filters.year
		},
        callback: function(r) {
            if (r.message) {
                // prepare the xml file for download
                var today = new Date();
                download("intrastat_" + today.getFullYear() + "-" + today.getMonth() + ".csv", r.message.content);
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
