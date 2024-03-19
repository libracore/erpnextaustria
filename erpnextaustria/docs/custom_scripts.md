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

    function download(filename, text) {
      var element = document.createElement('a');
      element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
      element.setAttribute('download', filename);

      element.style.display = 'none';
      document.body.appendChild(element);

      element.click();

      document.body.removeChild(element);
    }

    function download_csv(frm) {
        frappe.call({
            "method": "erpnextaustria.erpnextaustria.utils.get_general_ledger_csv",
            "args": {
                "fiscal_year": frm.doc.name,
                "company": "MyCompany"
            },
            "freeze": true,
            "freeze_message": __("Generating..."),
            "callback": function(response) {
                download(cur_frm.doc.name + ".csv", response.message);
            }
        });
        
    }
