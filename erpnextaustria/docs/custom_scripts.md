# Custom SCripts
## Fiscal Year
### Create CSV Export from a fiscla years

    frappe.ui.form.on('Fiscal Year', {
        refresh(frm) {
            frm.add_custom_button(__("CSV herunterladen"), function() {
                download_csv(frm);
            });
        }
    });

    function download_csv(frm) {
        // html-content of the label
        var url = "/api/method/erpnextaustria.erpnextaustria.utils.get_general_ledger_csv"  
                + "?fiscal_year=" + encodeURIComponent(frm.doc.name)
                + "&company=MyCompany";
        var w = window.open(
             frappe.urllib.get_full_url(url)
        );
        if (!w) {
            frappe.msgprint(__("Please enable pop-ups")); return;
        }
    }
