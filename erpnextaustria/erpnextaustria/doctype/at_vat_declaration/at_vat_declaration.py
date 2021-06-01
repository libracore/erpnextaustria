# -*- coding: utf-8 -*-
# Copyright (c) 2018-2021, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime
import pypdftk
from frappe.utils import get_bench_path

class ATVATDeclaration(Document):
    def on_submit(self):
        if self.auto_create_journal_entry:
            settings = frappe.get_doc("ERPNextAustria Settings", "ERPNextAustria Settings")
            if not settings.uva_accounts or len(settings.uva_accounts) == 0:
                frappe.msgprint( _("Unable to create journal entry: configuration missing"), _("Auto creation failed") )
            else:
                doc = frappe.get_doc({
                    'doctype': "Journal Entry",
                    'is_opening': "Yes",
                    'posting_date': self.end_date
                })
                total_tax = 0
                total_tax_account = None
                for a in settings.uva_accounts:
                    if a.uva_code == "Tax-Account":
                        total_tax_account = a.account
                    else:
                        # normal taxdes
                        if a.uva_code == "022":
                            total_tax += self.tax_normal
                            doc = append_tax(doc, a.account, self.tax_normal, 0)
                        elif a.uva_code == "029":
                            total_tax += self.tax_reduced_rate_1
                            doc = append_tax(doc, a.account, self.tax_reduced_rate_1, 0)
                        elif a.uva_code == "006":
                            total_tax += self.tax_reduced_rate_2
                            doc = append_tax(doc, a.account, self.tax_reduced_rate_2, 0)
                        elif a.uva_code == "037":
                            total_tax += self.tax_reduced_rate_3
                            doc = append_tax(doc, a.account, self.tax_reduced_rate_3, 0)
                        elif a.uva_code == "052":
                            total_tax += self.tax_additional_1
                            doc = append_tax(doc, a.account, self.tax_additional_1, 0)
                        elif a.uva_code == "007":
                            total_tax += self.tax_additional_2
                            doc = append_tax(doc, a.account, self.tax_additional_2, 0)
                        # other taxes
                        elif a.uva_code == "056":
                            total_tax += self.tax_056
                            doc = append_tax(doc, a.account, self.tax_056, 0)
                        elif a.uva_code == "057":
                            total_tax += self.tax_057
                            doc = append_tax(doc, a.account, self.tax_057, 0)
                        elif a.uva_code == "048":
                            total_tax += self.tax_048
                            doc = append_tax(doc, a.account, self.tax_048, 0)
                        elif a.uva_code == "044":
                            total_tax += self.tax_044
                            doc = append_tax(doc, a.account, self.tax_044, 0)
                        elif a.uva_code == "032":
                            total_tax += self.tax_032
                            doc = append_tax(doc, a.account, self.tax_032, 0)
                        # intercommunal
                        elif a.uva_code == "072":
                            total_tax += self.tax_inter_normal
                            doc = append_tax(doc, a.account, self.tax_inter_normal, 0)
                        elif a.uva_code == "073":
                            total_tax += self.tax_inter_reduced_1
                            doc = append_tax(doc, a.account, self.tax_inter_reduced_1, 0)
                        elif a.uva_code == "008":
                            total_tax += self.tax_inter_reduced_2
                            doc = append_tax(doc, a.account, self.tax_inter_reduced_2, 0)
                        elif a.uva_code == "088":
                            total_tax += self.tax_inter_reduced_3
                            doc = append_tax(doc, a.account, self.tax_inter_reduced_3, 0)
                        # pretax
                        elif a.uva_code == "060":
                            total_tax -= self.total_pretax
                            doc = append_tax(doc, a.account, 0, self.total_pretax)
                        elif a.uva_code == "061":
                            total_tax -= self.import_pretax
                            doc = append_tax(doc, a.account, 0, self.import_pretax)
                        elif a.uva_code == "083":
                            total_tax -= self.import_charge_pretax
                            doc = append_tax(doc, a.account, 0, self.import_charge_pretax)
                        elif a.uva_code == "065":
                            total_tax -= self.intercommunal_pretax
                            doc = append_tax(doc, a.account, 0, self.intercommunal_pretax)
                        elif a.uva_code == "066":
                            total_tax -= self.taxation_pretax
                            doc = append_tax(doc, a.account, 0, self.taxation_pretax)
                        elif a.uva_code == "082":
                            total_tax -= self.taxation_building_pretax
                            doc = append_tax(doc, a.account, 0, self.taxation_building_pretax)
                        elif a.uva_code == "087":
                            total_tax -= self.taxation_pretax_other_1
                            doc = append_tax(doc, a.account, 0, self.taxation_pretax_other_1)
                        elif a.uva_code == "089":
                            total_tax -= self.taxation_pretax_other_2
                            doc = append_tax(doc, a.account, 0, self.taxation_pretax_other_2)
                        elif a.uva_code == "064":
                            total_tax -= self.vehicles_pretax
                            doc = append_tax(doc, a.account, 0, self.vehicles_pretax)
                        elif a.uva_code == "062":
                            total_tax -= self.not_deductable_pretax
                            doc = append_tax(doc, a.account, 0, self.not_deductable_pretax)
                        elif a.uva_code == "063":
                            total_tax -= self.corrections_1
                            doc = append_tax(doc, a.account, 0, self.corrections_1)
                        elif a.uva_code == "067":
                            total_tax -= self.corrections_2
                            doc = append_tax(doc, a.account, 0, self.corrections_2)
                # actual tax on tax account
                doc = append_tax(doc, total_tax_account, 0, total_tax)
                doc.insert()
                self.journal_entry = doc.name
                self.save()
                doc.submit()
        return
        
    # generate xml export
    def generate_transfer_file(self):
        #try:
        fastnr = frappe.get_value("ERPNextAustria Settings", "ERPNextAustria Settings", "fastnr").replace('.', '')
        now = datetime.now()
        data = {
            'fastnr': fastnr,
            'datum': "{0:04d}-{1:02d}-{2:02d}".format(now.year, now.month, now.day),
            'zeit': "{0:02d}:{1:02d}:{2:02d}".format(now.hour, now.minute, now.second),
            'von': "{0}".format(self.start_date[0:7]),
            'bis': "{0}".format(self.end_date[0:7]),
            'kundeninfo': self.company,
            'revenue': self.revenue,
            'exports': self.exports,
            'inner_eu': self.inner_eu,
            'receiver_vat': self.receiver_vat,
            'amount_normal': self.amount_normal,
            'reduced_amount': self.reduced_amount,
            'tax_057': self.tax_057,
            'total_pretax': self.total_pretax,
            'import_pretax': self.import_pretax,
            'import_charge_pretax': self.import_charge_pretax,
            'intercommunla_pretax': self.intercommunal_pretax,
            'taxation_pretax': self.taxation_pretax,
            'intercommunal_revenue': self.intercommunal_revenue,
            'amount_inter_normal': self.amount_inter_normal
        }
        # render template
        content = frappe.render_template('erpnextaustria/erpnextaustria/doctype/at_vat_declaration/u30.html', data)
     
        return { 'content': content }
    #except IndexError:
    #    frappe.msgprint( _("Please select at least one payment."), _("Information") )
    #    return
    #except:
    #    frappe.throw( _("Error while generating xml. Make sure that you made required customisations to the DocTypes.") )
    #    return

def append_tax(doc, account, debit, credit):
    doc.append('accounts', {
        'account': account,
        'debit_in_account_currency': debit,
        'credit_in_account_currency': credit
    })
    return doc
    
# note: do not move below functions into the class, otherwise, saving values will be impossible
@frappe.whitelist()
def get_view_total(view_name, start_date, end_date, company="%"):
    # try to fetch total from VAT query
    if frappe.db.exists("AT VAT query", view_name):
        sql_query = ("""SELECT IFNULL(SUM(`s`.`base_grand_total`), 0) AS `total` 
                FROM ({query}) AS `s` 
                WHERE `s`.`posting_date` >= '{start_date}' 
                AND `s`.`posting_date` <= '{end_date}'""".format(
                query=frappe.get_value("AT VAT query", view_name, "query"),
                start_date=start_date, end_date=end_date).replace("{company}", company))        
    else:
        # fallback database view
        """ executes a tax lookup query for a total 
        
        """
        sql_query = ("""SELECT IFNULL(SUM(`base_grand_total`), 0) AS `total` 
                FROM `{0}` 
                WHERE `posting_date` >= '{1}' 
                AND `posting_date` <= '{2}'""".format(view_name, start_date, end_date))
    total = frappe.db.sql(sql_query, as_dict=True)
    return { 'total': total[0].total }

@frappe.whitelist()
def get_view_tax(view_name, start_date, end_date, company="%"):
    # try to fetch total from VAT query
    if frappe.db.exists("AT VAT query", view_name):
        sql_query = ("""SELECT IFNULL(SUM(`s`.`total_taxes_and_charges`), 0) AS `total` 
                FROM ({query}) AS `s` 
                WHERE `s`.`posting_date` >= '{start_date}' 
                AND `s`.`posting_date` <= '{end_date}'""".format(
                query=frappe.get_value("AT VAT query", view_name, "query"),
                start_date=start_date, end_date=end_date).replace("{company}", company))      
    else:
        # fallback database view
        """ executes a tax lookup query for a tax 
        
        """
        sql_query = ("""SELECT IFNULL(SUM(`total_taxes_and_charges`), 0) AS `total` 
                FROM `{0}` 
                WHERE `posting_date` >= '{1}' 
                AND `posting_date` <= '{2}'""".format(view_name, start_date, end_date))
    total = frappe.db.sql(sql_query, as_dict=True)
    return { 'total': total[0].total }
  
@frappe.whitelist()
def get_tax_rate(taxes_and_charges_template):
    sql_query = ("""SELECT `rate` 
        FROM `tabPurchase Taxes and Charges` 
        WHERE `parent` = '{0}' 
        ORDER BY `idx`;""".format(taxes_and_charges_template))
    result = frappe.db.sql(sql_query, as_dict=True)
    if result:
        return result[0].rate
    else:
        return 0

@frappe.whitelist()
def download_uva_pdf(uva):
    doc = frappe.get_doc("AT VAT Declaration", uva)
    # generate content
    company_address = get_company_address(doc.company)
    settings = frappe.get_doc("ERPNextAustria Settings", "ERPNextAustria Settings")
    tax_codes = settings.fastnr.split(".") if settings.fastnr else ['00', '000', '0000']
    data = {
        'Text01': settings.finanzamt,
        'Checkbox00a': 1,
        'Zahl03': tax_codes[0],
        'Zahl02_1': tax_codes[1],
        'Zahl02_2': tax_codes[2],
        'Text01_m': "{0}".format(doc.start_date)[5:7],         # month
        'Text03': doc.company,
        'Text05': company_address.address_line1 if company_address else "",
        'Text07b': 'AT',
        'Text07c': company_address.phone if company_address else "",
        'Text07d': company_address.pincode if company_address else "",
        'Text07e': company_address.city if company_address else "",
        'Zahl101': get_at_value(doc.revenue),                  # 000
        'Zahl102': get_at_value(doc.self_consumption),         # 001
        'Zahl103': get_at_value(doc.receiver_vat),             # 021
        'Zahl104': get_at_value(doc.total_revenue),            # (4.4)
        'Zahl105': get_at_value(doc.exports),                  # 011
        'Zahl106': get_at_value(doc.subcontracting),           # 012
        'Zahl107': get_at_value(doc.cross_border),             # 015
        'Zahl108': get_at_value(doc.inner_eu),                 # 017
        'Zahl109': get_at_value(doc.vehicles_without_uid),     # 018
        'Zahl110': get_at_value(doc.property_revenue),         # 019
        'Zahl111': get_at_value(doc.small_businesses),         # 016
        'Zahl113': get_at_value(doc.tax_free_revenue),         # 020
        'Zahl114': get_at_value(doc.total_amount),             # (4.13)
        'Zahl115a': get_at_value(doc.amount_normal),           # 022
        'Zahl115b': get_at_value(doc.tax_normal),              # 022
        'Zahl116a': get_at_value(doc.reduced_amount),          # 029
        'Zahl116b': get_at_value(doc.tax_reduced_rate_1),      # 029
        'Zahl117a': get_at_value(doc.reduced_amount_2),        # 006
        'Zahl117b': get_at_value(doc.tax_reduced_rate_2),      # 006
        'Zahl118a': get_at_value(doc.reduced_amount_3),        # 037
        'Zahl118b': get_at_value(doc.tax_reduced_rate_3),      # 037
        'Zahl119a': get_at_value(doc.amount_additional_1),     # 052
        'Zahl119b': get_at_value(doc.tax_additional_1),        # 052
        'Zahl120a': get_at_value(doc.amount_additional_2),     # 007
        'Zahl120b': get_at_value(doc.tax_additional_2),        # 007
        'Zahl121a': get_at_value(0),                           # 009
        'Zahl121b': get_at_value(0),                           # 009
        'Zahl123': get_at_value(doc.tax_056),                  # 056
        'Zahl124': get_at_value(doc.tax_057),                  # 057
        'Zahl125': get_at_value(doc.tax_048),                  # 048
        'Zahl125a': get_at_value(doc.tax_044),                 # 044
        'Zahl125b': get_at_value(doc.tax_032),                 # 032
        'Zahl126': get_at_value(doc.intercommunal_revenue),    # 070
        'Zahl127': get_at_value(doc.taxfree_intercommunal),    # 071
        'Zahl127a': get_at_value(doc.total_intercommunal),     # (4.28)
        'Zahl128a': get_at_value(doc.amount_inter_normal),     # 072
        'Zahl128b': get_at_value(doc.tax_inter_normal),        # 072
        'Zahl129a': get_at_value(doc.amount_inter_reduced_1),  # 073
        'Zahl129b': get_at_value(doc.tax_inter_reduced_1),     # 073
        'Zahl129a_1': get_at_value(doc.amount_inter_reduced_2),# 008
        'Zahl129b_1': get_at_value(doc.tax_inter_reduced_2),   # 008
        'Zahl130a': get_at_value(doc.amount_inter_reduced_3),  # 088
        'Zahl130b': get_at_value(doc.tax_inter_reduced_3),     # 088
        'Zahl130aa': get_at_value(0),                          # 010
        'Zahl130bb': get_at_value(0),                          # 010
        'Zahl131': get_at_value(doc.external_taxation),        # 076
        'Zahl132': get_at_value(doc.internal_taxation),        # 077
        'Zahl133': get_at_value(doc.total_pretax),             # 060
        'Zahl134': get_at_value(doc.import_pretax),            # 061
        'Zahl134a': get_at_value(doc.import_charge_pretax),    # 083
        'Zahl135': get_at_value(doc.intercommunal_pretax),     # 065
        'Zahl136': get_at_value(doc.taxation_pretax),          # 066
        'Zahl136a': get_at_value(doc.taxation_building_pretax),# 082
        'Zahl137': get_at_value(doc.taxation_pretax_other_1),  # 087
        'Zahl137a': get_at_value(doc.taxation_pretax_other_2), # 089
        'Zahl138': get_at_value(doc.vehicles_pretax),          # 064
        'Zahl139': get_at_value(doc.non_deductable_pretax),    # 062
        'Zahl140': get_at_value(doc.corrections_1),            # 063
        'Zahl141': get_at_value(doc.corrections_2),            # 067
        'Zahl142': get_at_value(doc.total_deductable_pretax),  # (5.13)
        'Text143': doc.description_other_correction,
        'Zahl143': get_at_value(doc.tax_other_corrections),    # 090
        'Zahl144': get_at_value(doc.total_tax_due),            # 095
        'Checkbox100X': 2 if doc.total_tax_due > 0 else 0,      # (7.1)
        'Tagesdatum2': datetime.now().strftime("%d.%m.%Y")     # date
    }
    # generate pdf
    generated_pdf = pypdftk.fill_form(get_bench_path() + '/apps/erpnextaustria/erpnextaustria/templates/pdf/U30.pdf', data)
    with open(generated_pdf, mode='rb') as file:
        pdf_data = file.read()
    # return content
    frappe.local.response.filename = "{name}.pdf".format(name=uva.replace(" ", "-").replace("/", "-"))
    frappe.local.response.filecontent = pdf_data
    frappe.local.response.type = "download"
    return

def get_at_value(v):
    return "{0:,.2f}".format(v).replace(",", "'").replace(".", ",").replace("'", "")
    
def get_company_address(target_name):
    sql_query = """SELECT 
            `tabAddress`.`address_line1`, 
            `tabAddress`.`address_line2`, 
            `tabAddress`.`pincode`, 
            `tabAddress`.`city`, 
            `tabAddress`.`county`,
            `tabAddress`.`country`, 
            `tabAddress`.`phone`, 
            UPPER(`tabCountry`.`code`) AS `country_code`, 
            `tabAddress`.`is_primary_address`
        FROM `tabDynamic Link` 
        LEFT JOIN `tabAddress` ON `tabDynamic Link`.`parent` = `tabAddress`.`name`
        LEFT JOIN `tabCountry` ON `tabAddress`.`country` = `tabCountry`.`name`
        WHERE `link_doctype` = 'Company' AND `link_name` = '{name}'
        ORDER BY `tabAddress`.`is_primary_address` DESC
        LIMIT 1;""".format(name=target_name)
    try:
        return frappe.db.sql(sql_query, as_dict=True)[0]
    except:
        return None
