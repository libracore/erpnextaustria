# -*- coding: utf-8 -*-
# Copyright (c) 2018, Fink Zeitsysteme/libracore and contributors
# For license information, please see license.txt

# imports
from zeep import Client

# UID validation
def check_uid(uid):
    client = Client('http://ec.europa.eu/taxation_customs/vies/checkVatService.wsdl')
    result = client.service.checkVat('AT', 'U36401407')
    print(result.valid)
    return result.valid
