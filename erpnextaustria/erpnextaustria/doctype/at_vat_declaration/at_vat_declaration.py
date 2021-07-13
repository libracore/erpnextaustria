# -*- coding: utf-8 -*-
# Copyright (c) 2018-2021, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

from datetime import datetime
import pypdftk

import frappe
from frappe import _
from frappe.utils import get_bench_path
from frappe.model.document import Document
from frappe.contacts.doctype.address.address import get_default_address

class ATVATDeclaration(Document):
    def on_submit(self):
        if self.auto_create_journal_entry:
            self.create_journal_entry()

    def create_journal_entry(self):
        FIELDS_BY_CODE = { # uva_code: (debit_field, credit_field)

            # normal taxes
            "022": ("tax_normal", None),
            "029": ("tax_reduced_rate_1", None),
            "006": ("tax_reduced_rate_2", None),
            "037": ("tax_reduced_rate_3", None),
            "052": ("tax_additional_1", None),
            "007": ("tax_additional_2", None),

            # other taxes
            "056": ("tax_056", None),
            "057": ("tax_057", None),
            "048": ("tax_048", None),
            "044": ("tax_044", None),
            "032": ("tax_032", None),

            # intercommunal
            "072": ("tax_inter_normal", None),
            "073": ("tax_inter_reduced_1", None),
            "008": ("tax_inter_reduced_2", None),
            "088": ("tax_inter_reduced_3", None),

            # pretax
            "060": (None, "total_pretax"),
            "061": (None, "import_pretax"),
            "083": (None, "import_charge_pretax"),
            "065": (None, "intercommunal_pretax"),
            "082": (None, "taxation_building_pretax"),
            "087": (None, "taxation_pretax_other_1"),
            "089": (None, "taxation_pretax_other_2"),
            "064": (None, "vehicles_pretax"),
            "062": (None, "not_deductable_pretax"),
            "063": (None, "corrections_1"),
            "067": (None, "corrections_2")
        }

        settings = frappe.get_doc("ERPNextAustria Settings", "ERPNextAustria Settings")
        if not settings.uva_accounts or len(settings.uva_accounts) == 0:
            frappe.msgprint( _("Unable to create journal entry: configuration missing"), _("Auto creation failed") )
            return

        journal_entry = frappe.get_doc({
            'doctype': "Journal Entry",
            'is_opening': "Yes",
            'posting_date': self.end_date
        })
        total_tax_account = None

        for a in settings.uva_accounts:
            if a.uva_code == "Tax-Account":
                total_tax_account = a.account
                continue

            fields = FIELDS_BY_CODE.get(a.uva_code)
            if not fields:
                continue

            debit = fields[0]
            credit = fields[1]

            if debit:
                journal_entry.append('accounts', {
                    'account': a.account,
                    'debit_in_account_currency': self.get(debit)
                })

            if credit:
                journal_entry.append('accounts', {
                    'account': a.account,
                    'credit_in_account_currency': self.get(credit)
                })

        # actual tax on tax account
        journal_entry.set_total_debit_credit()
        journal_entry.append('accounts', {
            'account': total_tax_account,
            'credit_in_account_currency': journal_entry.difference
        })

        journal_entry.insert()

        self.journal_entry = journal_entry.name
        self.flags.ignore_validate = True
        self.flags.ignore_validate_update_after_submit = True
        self.save()

        journal_entry.submit()

    def generate_transfer_file(self):
        """Generate XML export."""
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
        'Zahl101': doc.revenue,                  # 000
        'Zahl102': doc.self_consumption,         # 001
        'Zahl103': doc.receiver_vat,             # 021
        'Zahl104': doc.total_revenue,            # (4.4)
        'Zahl105': doc.exports,                  # 011
        'Zahl106': doc.subcontracting,           # 012
        'Zahl107': doc.cross_border,             # 015
        'Zahl108': doc.inner_eu,                 # 017
        'Zahl109': doc.vehicles_without_uid,     # 018
        'Zahl110': doc.property_revenue,         # 019
        'Zahl111': doc.small_businesses,         # 016
        'Zahl113': doc.tax_free_revenue,         # 020
        'Zahl114': doc.total_amount,             # (4.13)
        'Zahl115a': doc.amount_normal,           # 022
        'Zahl115b': doc.tax_normal,              # 022
        'Zahl116a': doc.reduced_amount,          # 029
        'Zahl116b': doc.tax_reduced_rate_1,      # 029
        'Zahl117a': doc.reduced_amount_2,        # 006
        'Zahl117b': doc.tax_reduced_rate_2,      # 006
        'Zahl118a': doc.reduced_amount_3,        # 037
        'Zahl118b': doc.tax_reduced_rate_3,      # 037
        'Zahl119a': doc.amount_additional_1,     # 052
        'Zahl119b': doc.tax_additional_1,        # 052
        'Zahl120a': doc.amount_additional_2,     # 007
        'Zahl120b': doc.tax_additional_2,        # 007
        'Zahl121a': 0,                           # 009
        'Zahl121b': 0,                           # 009
        'Zahl123': doc.tax_056,                  # 056
        'Zahl124': doc.tax_057,                  # 057
        'Zahl125': doc.tax_048,                  # 048
        'Zahl125a': doc.tax_044,                 # 044
        'Zahl125b': doc.tax_032,                 # 032
        'Zahl126': doc.intercommunal_revenue,    # 070
        'Zahl127': doc.taxfree_intercommunal,    # 071
        'Zahl127a': doc.total_intercommunal,     # (4.28)
        'Zahl128a': doc.amount_inter_normal,     # 072
        'Zahl128b': doc.tax_inter_normal,        # 072
        'Zahl129a': doc.amount_inter_reduced_1,  # 073
        'Zahl129b': doc.tax_inter_reduced_1,     # 073
        'Zahl129a_1': doc.amount_inter_reduced_2,# 008
        'Zahl129b_1': doc.tax_inter_reduced_2,   # 008
        'Zahl130a': doc.amount_inter_reduced_3,  # 088
        'Zahl130b': doc.tax_inter_reduced_3,     # 088
        'Zahl130aa': 0,                          # 010
        'Zahl130bb': 0,                          # 010
        'Zahl131': doc.external_taxation,        # 076
        'Zahl132': doc.internal_taxation,        # 077
        'Zahl133': doc.total_pretax,             # 060
        'Zahl134': doc.import_pretax,            # 061
        'Zahl134a': doc.import_charge_pretax,    # 083
        'Zahl135': doc.intercommunal_pretax,     # 065
        'Zahl136': doc.taxation_pretax,          # 066
        'Zahl136a': doc.taxation_building_pretax,# 082
        'Zahl137': doc.taxation_pretax_other_1,  # 087
        'Zahl137a': doc.taxation_pretax_other_2, # 089
        'Zahl138': doc.vehicles_pretax,          # 064
        'Zahl139': doc.non_deductable_pretax,    # 062
        'Zahl140': doc.corrections_1,            # 063
        'Zahl141': doc.corrections_2,            # 067
        'Zahl142': doc.total_deductable_pretax,  # (5.13)
        'Text143': doc.description_other_correction,
        'Zahl143': doc.tax_other_corrections,    # 090
        'Zahl144': doc.total_tax_due,            # 095
        'Checkbox100X': 2 if doc.total_tax_due > 0 else 0,      # (7.1)
        'Tagesdatum2': datetime.now().strftime("%d.%m.%Y")     # date
    }

    # Nicely format the numbers
    for key, value in data.items():
        if "Zahl1" in key:
            data[key] = "{0:,.2f}".format(value).replace(",", "'").replace(".", ",").replace("'", "")

    # generate pdf
    generated_pdf = pypdftk.fill_form(get_bench_path() + '/apps/erpnextaustria/erpnextaustria/templates/pdf/U30.pdf', data)
    with open(generated_pdf, mode='rb') as file:
        pdf_data = file.read()

    # return content
    frappe.local.response.filename = "{name}.pdf".format(name=uva.replace(" ", "-").replace("/", "-"))
    frappe.local.response.filecontent = pdf_data
    frappe.local.response.type = "download"


def get_company_address(company):
    default_address = get_default_address("Company", company)
    if not default_address:
        return

    address_doc = frappe.get_doc("Address", default_address)
    address_dict = address_doc.as_dict()
    address_dict["country_code"] = frappe.get_value("Country", address_dict.country, "code")

    return address_dict
