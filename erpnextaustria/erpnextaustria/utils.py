# -*- coding: utf-8 -*-
# Copyright (c) 2018, Fink Zeitsysteme/libracore and contributors
# For license information, please see license.txt

# imports
import frappe
from zeep import Client

# UID validation
#
# Returns a dict with the attribute 'valid' = "True" or "False"
@frappe.whitelist()
def check_uid(uid):
    client = Client('http://ec.europa.eu/taxation_customs/vies/checkVatService.wsdl')
    result = client.service.checkVat(uid[0:2], uid[2:])
    return result.valid
