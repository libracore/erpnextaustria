// Copyright (c) 2018, libracore and contributors
// For license information, please see license.txt

frappe.ui.form.on('AT VAT Declaration', {
	refresh: function(frm) {
        frm.add_custom_button(__("Get values"), function() 
		{
			get_values(frm);
		});
        frm.add_custom_button(__("Recalculate"), function() 
		{
			update_total_revenue(frm);
		});
        frm.add_custom_button(__("Download XML"), function() 
		{
			download_xml(frm);
		});
        frm.add_custom_button(__("Show data"), function() 
		{
			console.log(frm.doc);
		});     
           
        if (frm.doc.__islocal) {
            // this function is called when a new VAT declaration is created
            // get current month (0..11)
            var d = new Date();
            var n = d.getMonth();
            // define title as Qn YYYY of the last complete quarter
            var title = " / " + d.getFullYear();
            if ((n > (-1)) && (n < 3)) {
                title = "Q04 / " + (d.getFullYear() - 1);
                frm.set_value('start_date', (d.getFullYear() - 1) + "-10-01");
                frm.set_value('end_date', (d.getFullYear() - 1) + "-12-31");
            } else if ((n > (2)) && (n < 6)) {
                title = "Q01" + title;
                frm.set_value('start_date', d.getFullYear() + "-01-01");
                frm.set_value('end_date', d.getFullYear() + "-03-31");
            } else if ((n > (5)) && (n < 9)) {
                title = "Q02" + title;
                frm.set_value('start_date', d.getFullYear() + "-04-01");
                frm.set_value('end_date', d.getFullYear() + "-06-30");
            } else {
                title = "Q03" + title;
                frm.set_value('start_date', d.getFullYear() + "-07-01");
                frm.set_value('end_date', d.getFullYear() + "-09-30");
            } 

            frm.set_value('title', title);
        }
        
        // recalculate fresh values
        update_total_revenue(frm);
    },
    validate: function(frm) {
        console.log(frm.doc);
    }
});

// retrieve values from database
function get_values(frm) {
    // Revenue
    get_total(frm, "viewATVAT_000", 'revenue');
    get_total(frm, "viewATVAT_011", 'exports');
    get_total(frm, "viewATVAT_017", 'inner_eu');
    get_total(frm, "viewATVAT_021", 'receiver_vat');
    // Revenue at normal rate
    get_total(frm, "viewATVAT_022", 'amount_normal');
    get_total(frm, "viewATVAT_029", 'reduced_amount');
    // Intercommunal revenue 
    get_total(frm, "viewATVAT_070", 'intercommunal_revenue');
    get_total(frm, "viewATVAT_072", 'amount_inter_normal');
    // Pretax
    get_tax(frm, "viewATVAT_060", 'total_pretax');
    get_tax(frm, "viewATVAT_061", 'import_pretax');
    get_tax(frm, "viewATVAT_065", 'intercommunal_pretax');
    get_tax(frm, "viewATVAT_083", 'import_charge_pretax');
    // reverse charge
    get_tax(frm, "viewATVAT_057", 'tax_057');
    get_tax(frm, "viewATVAT_066", 'taxation_pretax');
    
    // Recalculate
    update_total_revenue(frm);
}

// change handlers
frappe.ui.form.on('AT VAT Declaration', {
        'revenue':              function(frm) { update_total_revenue(frm) }, 
        'self_consumption':     function(frm) { update_total_revenue(frm) }, 
        'receiver_vat':         function(frm) { update_total_revenue(frm) },
        'intercommunal_revenue': function(frm) { update_total_revenue(frm) },
        'taxfree_intercommunal': function(frm) { update_total_revenue(frm) },
        'exports':              function(frm) { update_total_amount(frm) }, 
        'subcontracting':       function(frm) { update_total_amount(frm) }, 
        'cross_border':         function(frm) { update_total_amount(frm) }, 
        'inner_eu':             function(frm) { update_total_amount(frm) },  
        'vehicles_without_uid': function(frm) { update_total_amount(frm) },
        'property_revenue':     function(frm) { update_total_amount(frm) },
        'small_business':       function(frm) { update_total_amount(frm) },
        'taxfree_revenue':      function(frm) { update_total_amount(frm) },
        'amount_normal':        function(frm) { update_tax_amounts(frm) },
        'reduced_amount':       function(frm) { update_tax_amounts(frm) },
        'reduced_amount_2':     function(frm) { update_tax_amounts(frm) },
        'reduced_amount_3':     function(frm) { update_tax_amounts(frm) },
        'amount_additional_1':  function(frm) { update_tax_amounts(frm) },
        'amount_additional_2':  function(frm) { update_tax_amounts(frm) },
        'amount_inter_normal':  function(frm) { update_tax_amounts(frm) },
        'amount_inter_reduced_1':  function(frm) { update_tax_amounts(frm) },
        'amount_inter_reduced_2':  function(frm) { update_tax_amounts(frm) },
        'amount_inter_reduced_3':  function(frm) { update_tax_amounts(frm) },
        'total_pretax':         function(frm) { update_pretax(frm) },
        'import_pretax':        function(frm) { update_pretax(frm) },
        'import_charge_pretax': function(frm) { update_pretax(frm) },
        'intercommunal_pretax': function(frm) { update_pretax(frm) },
        'taxation_pretax':      function(frm) { update_pretax(frm) },
        'taxation_building_pretax': function(frm) { update_pretax(frm) },
        'taxation_pretax_other_1':  function(frm) { update_pretax(frm) },
        'taxation_pretax_other_2':  function(frm) { update_pretax(frm) },
        'vehicles_pretax':      function(frm) { update_pretax(frm) },
        'non_deductible_pretax':    function(frm) { update_pretax(frm) },
        'corrections_1':        function(frm) { update_pretax(frm) },
        'corrections_2':        function(frm) { update_pretax(frm) },
        'tax_other_corrections':    function(frm) { update_tax_due(frm) }
    }
);

function float(value) {
    var number = 0;
    number = parseFloat(value);
    if (isNaN(number)) {
        number = 0;
    }
    return number;
}

// Update total revenue
function update_total_revenue(frm) {
    var total_revenue = float(frm.doc.revenue) 
        + float(frm.doc.self_consumption)
        - float(frm.doc.receiver_vat);
    frm.set_value('total_revenue', total_revenue); 

    var total_inter_revenue = float(frm.doc.intercommunal_revenue) 
        - float(frm.doc.taxfree_intercommunal);
    frm.set_value('total_intercommunal', total_inter_revenue); 
        
    cur_frm.refresh_fields('total_revenue', 'total_intercommunal');
    // cascade change: recalculate total amount
    update_total_amount(frm); 
    
}

// Update total amount
function update_total_amount(frm) {
    var total_amount = float(frm.doc.total_revenue) 
        - float(frm.doc.exports) 
        - float(frm.doc.subcontracting)
        - float(frm.doc.cross_border)
        - float(frm.doc.inner_eu)
        - float(frm.doc.vehicles_without_uid)
        - float(frm.doc.property_revenue)
        - float(frm.doc.small_business)
        - float(frm.doc.taxfree_revenue);
    frm.set_value('total_amount', total_amount);    
    
    cur_frm.refresh_fields('total_amount');
    // cascade change: taxes
    update_tax_amounts(frm);
}

// Recalculate tax amount based on inputs
function update_tax_amounts(frm) {
    frm.set_value('tax_normal', (0.2) * float(frm.doc.amount_normal));
    frm.set_value('tax_reduced_rate_1', (0.1) * float(frm.doc.reduced_amount));
    frm.set_value('tax_reduced_rate_2', (0.13) * float(frm.doc.reduced_amount_2));
    frm.set_value('tax_reduced_rate_3', (0.19) * float(frm.doc.reduced_amount_3));
    frm.set_value('tax_additional_1', (0.10) * float(frm.doc.amount_additional_1));
    frm.set_value('tax_additional_2', (0.07) * float(frm.doc.amount_additional_2));
    frm.set_value('tax_inter_normal', (0.2) * float(frm.doc.amount_inter_normal));
    frm.set_value('tax_inter_reduced_1', (0.1) * float(frm.doc.amount_inter_reduced_1));
    frm.set_value('tax_inter_reduced_2', (0.13) * float(frm.doc.amount_inter_reduced_2));
    frm.set_value('tax_inter_reduced_3', (0.19) * float(frm.doc.amount_inter_reduced_3));
    
    cur_frm.refresh_fields('tax_normal', 
        'tax_reduced_rate_1', 
        'tax_reduced_rate_2', 
        'tax_reduced_rate_3', 
        'tax_additional_1', 
        'tax_additional_2', 
        'tax_inter_normal', 
        'tax_inter_reduced_1', 
        'tax_inter_reduced_2', 
        'tax_inter_reduced_3');
        
    // cascade change: pretax
    update_pretax(frm);
}

// Update total amount
function update_pretax(frm) {
    var total_pretax = (-1) * float(frm.doc.total_pretax) 
        - float(frm.doc.import_pretax) 
        - float(frm.doc.import_charge_pretax)
        - float(frm.doc.intercommunal_pretax)
        - float(frm.doc.taxation_pretax)
        - float(frm.doc.taxation_building_pretax)
        - float(frm.doc.taxation_pretax_other_1)
        - float(frm.doc.taxation_pretax_other_2)
        - float(frm.doc.vehicles_pretax)
        + float(frm.doc.non_deductible_pretax)
        + float(frm.doc.corrections_1)
        + float(frm.doc.corrections_2);
    frm.set_value('total_deductable_pretax', total_pretax);    
    
    cur_frm.refresh_fields('total_deductable_pretax');
    // cascade change: taxes
    update_tax_due(frm);
}

// Update tax due
function update_tax_due(frm) {
    var total_tax_due = float(frm.doc.tax_normal) 
        + float(frm.doc.tax_reduced_rate_1) 
        + float(frm.doc.tax_reduced_rate_2)
        + float(frm.doc.tax_reduced_rate_3)
        + float(frm.doc.tax_additional_1)
        + float(frm.doc.tax_additional_2)
        + float(frm.doc.tax_056)
        + float(frm.doc.tax_057)
        + float(frm.doc.tax_048)
        + float(frm.doc.tax_044)
        + float(frm.doc.tax_032)
        + float(frm.doc.tax_inter_normal)
        + float(frm.doc.tax_inter_reduced_1)
        + float(frm.doc.tax_inter_reduced_2)
        + float(frm.doc.tax_inter_reduced_3)
        - float(frm.doc.total_deductable_pretax)
        + float(frm.doc.tax_other_corrections);
    cur_frm.set_value('total_tax_due', total_tax_due);    
    cur_frm.refresh_fields('total_tax_due');
}

/* view: view to use
 * target: target field
 */
function get_total(frm, view, target) {
    // total revenues is the sum of all base grnad totals in the period
    frappe.call({
        method: 'erpnextaustria.erpnextaustria.doctype.at_vat_declaration.at_vat_declaration.get_view_total',
        args: { 
            start_date: frm.doc.start_date,
            end_date: frm.doc.end_date,
            view_name: view
        },
        callback: function(r) {
            if (r.message) {
                frm.set_value(target, r.message.total);
            }
        }
    }); 
}

/* view: view to use
 * target: target field
 */
function get_tax(frm, view, target) {
    // total tax is the sum of all taxes in the period
    frappe.call({
        method: 'erpnextaustria.erpnextaustria.doctype.at_vat_declaration.at_vat_declaration.get_view_tax',
        args: { 
            start_date: frm.doc.start_date,
            end_date: frm.doc.end_date,
            view_name: view
        },
        callback: function(r) {
            if (r.message) {
                frm.set_value(target, r.message.total);
            }
        }
    }); 
}

/* download xml form */
function download_xml(frm) {
    // generate U30 xml file
    frappe.call({
        method: 'generate_transfer_file',
        doc: frm.doc,
        callback: function(r) {
            if (r.message) {
                // prepare the xml file for download
                var today = new Date();
                download("u30_" + today.getFullYear() + "-" + today.getMonth() + ".xml", r.message.content);
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
