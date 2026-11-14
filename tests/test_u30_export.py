# -*- coding: utf-8 -*-
# Copyright (c) 2026, libracore and contributors
# For license information, please see license.txt

import copy
import hashlib
import importlib.util
import os
from datetime import date, datetime
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
from urllib.request import urlopen

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from lxml import etree

from erpnextaustria.erpnextaustria.doctype.at_vat_declaration.u30 import (
    SCHEMA_URLS, get_schema_version, get_transfer_data
)


ROOT = Path(__file__).resolve().parents[1]
DOCTYPE = ROOT / 'erpnextaustria/erpnextaustria/doctype/at_vat_declaration'
HASHES = {
    '01_2022': '484bdff6e41ab80a18abe7331cc2720494dbf09d0438eaedd0a8db6be5124551',
    '07_2026': 'e51a69c99568f2d9fbccf9271d6243d9880588561a30746303ad6c23d646f757'
}


class Declaration(dict):
    def __getattr__(self, key):
        return self.get(key)


class TestU30Export(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schemas = {}
        for version, url in SCHEMA_URLS.items():
            # Original BMF schemas: download rather than redistribute/relicense.
            directory = os.environ.get('U30_XSD_DIR')
            if directory:
                data = (Path(directory) / url.rsplit('/', 1)[1]).read_bytes()
            else:
                with urlopen(url, timeout=20) as response:
                    data = response.read(256 * 1024)
            if hashlib.sha256(data).hexdigest() != HASHES[version]:
                raise AssertionError('BMF schema changed: review source and hash for ' + version)
            parser = etree.XMLParser(resolve_entities=False, no_network=True)
            cls.schemas[version] = etree.XMLSchema(etree.fromstring(data, parser))
        cls.environment = Environment(
            loader=FileSystemLoader(str(ROOT)), undefined=StrictUndefined
        )

    def document(self, **values):
        doc = Declaration(start_date='2025-10-01', end_date='2025-12-31',
                          company='Synthetic & Co <Test>')
        doc.update(values)
        return doc

    def render(self, doc):
        data = get_transfer_data(doc, '12.345.6789', datetime(2026, 11, 14, 12, 30))
        template = 'erpnextaustria/erpnextaustria/doctype/at_vat_declaration/u30.html'
        xml = etree.fromstring(self.environment.get_template(template).render(data).encode('utf-8'))
        version = get_schema_version(doc.start_date, doc.end_date)
        self.schemas[version].assertValid(xml)
        self.assertEqual(xml.get('{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation'),
                         SCHEMA_URLS[version])
        return xml

    def amounts(self, xml):
        return {node.tag: node.text for node in xml.iter() if node.tag.startswith('KZ')}

    def test_small_business(self):
        for start, end in [('2025-10-01', '2025-12-31'), ('2026-07-01', '2026-09-30')]:
            with self.subTest(start=start):
                xml = self.render(self.document(start_date=start, end_date=end,
                                               revenue=1500, small_businesses=1500))
                self.assertEqual(self.amounts(xml), {'KZ000': '1500.00', 'KZ016': '1500.00'})

    def test_reverse_charge_without_input_tax_entitlement(self):
        for start, end in [('2026-04-01', '2026-06-30'), ('2026-07-01', '2026-09-30')]:
            with self.subTest(start=start):
                xml = self.render(self.document(start_date=start, end_date=end, tax_057=48,
                                               taxation_pretax=0))
                self.assertEqual(self.amounts(xml), {'KZ000': '0.00', 'KZ057': '48.00'})
                self.assertEqual(xml.findtext('.//VERSTEUERT/KZ057'), '48.00')
                self.assertIsNone(xml.find('.//VORSTEUER'))

    def test_standard_taxation_and_acquisition_order(self):
        xml = self.render(self.document(
            revenue=1600, receiver_vat=100, exports=200, inner_eu=100,
            amount_normal=1000, reduced_amount=200, tax_057=20,
            intercommunal_revenue=400, amount_inter_normal=400,
            total_pretax=50, import_pretax=10, import_charge_pretax=5,
            intercommunal_pretax=80, taxation_pretax=20
        ))
        amounts = self.amounts(xml)
        self.assertEqual(amounts['KZ065'], '80.00')
        self.assertEqual(amounts['KZ066'], '20.00')
        self.assertEqual(amounts['KZ021'], '100.00')
        self.assertEqual(xml.findtext('.//KUNDENINFO'), 'Synthetic & Co <Test>')
        self.assertIsNone(xml.find('.//KZ095'))

    def test_q3_2026_new_fields_and_order(self):
        xml = self.render(self.document(
            start_date='2026-07-01', end_date='2026-09-30', revenue=1600,
            amount_normal=1000, amount_124=400, reduced_amount=200,
            intercommunal_revenue=500, amount_inter_normal=300,
            amount_125=150, amount_inter_reduced_1=50, total_pretax=40
        ))
        self.assertEqual(self.amounts(xml)['KZ124'], '400.00')
        self.assertEqual(self.amounts(xml)['KZ125'], '150.00')
        self.assertFalse(self.schemas['01_2022'].validate(xml))

    def test_null_missing_and_rounded_zero_values(self):
        xml = self.render(self.document(revenue=None, exports='0.00', tax_057=None,
                                       small_businesses=0, taxation_pretax=0.004,
                                       amount_124=0, amount_125=None))
        self.assertEqual(self.amounts(xml), {'KZ000': '0.00'})
        self.assertIsNone(xml.find('.//STEUERFREI'))
        self.assertIsNone(xml.find('.//VERSTEUERT'))
        self.assertIsNone(xml.find('.//INNERGEMEINSCHAFTLICHE_ERWERBE'))

    def test_other_existing_declaration_fields(self):
        xml = self.render(self.document(
            self_consumption=12, subcontracting=5, cross_border=6,
            vehicles_without_uid=7, property_revenue=8, tax_free_revenue=9,
            reduced_amount_2=100, reduced_amount_3=200, amount_additional_1=30,
            amount_additional_2=40, tax_056=5, tax_048=6, tax_044=7, tax_032=8,
            taxfree_intercommunal=9, amount_inter_reduced_2=10,
            amount_inter_reduced_3=11, external_taxation=12, internal_taxation=13,
            taxation_building_pretax=14, taxation_pretax_other_1=15,
            taxation_pretax_other_2=16, vehicles_pretax=17,
            non_deductable_pretax=18, corrections_1=-19, corrections_2=20,
            tax_other_corrections=-21
        ))
        amounts = self.amounts(xml)
        self.assertEqual(amounts['KZ001'], '12.00')
        self.assertEqual(amounts['KZ062'], '18.00')
        self.assertEqual(amounts['KZ063'], '-19.00')
        self.assertEqual(amounts['KZ090'], '-21.00')

    def test_schema_boundaries_and_date_objects(self):
        for start, end, expected in [
            ('2022-01-01', '2022-01-31', '01_2022'),
            ('2026-06-01', '2026-06-30', '01_2022'),
            ('2026-07-01', '2026-07-31', '07_2026'),
            (date(2027, 1, 1), date(2027, 3, 31), '07_2026')
        ]:
            with self.subTest(start=start):
                self.assertEqual(get_schema_version(start, end), expected)
                self.render(self.document(start_date=start, end_date=end))

    def test_reject_new_fields_before_july_2026(self):
        for field in ('amount_124', 'amount_125'):
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'July 2026'):
                get_transfer_data(self.document(**{field: 10}), '123456789', datetime.now())

    def test_reject_unsupported_periods(self):
        for start, end in [
            ('2021-12-01', '2021-12-31'), ('2026-06-01', '2026-07-31'),
            ('2026-07-02', '2026-09-30'), ('2026-07-01', '2026-09-29'),
            ('2026-09-01', '2026-07-31'), ('2026-01-01', '2026-12-31')
        ]:
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                get_schema_version(start, end)

    def test_xsd_rejects_original_regressions(self):
        xml = self.render(self.document(receiver_vat=10, exports=20, tax_057=5,
                                       intercommunal_revenue=100, total_pretax=10))
        bad = copy.deepcopy(xml)
        bad.find('.//KZ011').text = '0.00'
        self.assertFalse(self.schemas['01_2022'].validate(bad))
        bad = copy.deepcopy(xml)
        group = bad.find('.//LIEFERUNGEN_LEISTUNGEN_EIGENVERBRAUCH')
        group.append(group.find('KZ021'))
        self.assertFalse(self.schemas['01_2022'].validate(bad))
        bad = copy.deepcopy(xml)
        declaration = bad.find('ERKLAERUNG')
        declaration.append(declaration.find('INNERGEMEINSCHAFTLICHE_ERWERBE'))
        self.assertFalse(self.schemas['01_2022'].validate(bad))
        bad = copy.deepcopy(xml)
        bad.find('.//VORSTEUER').append(bad.find('.//KZ057'))
        self.assertFalse(self.schemas['01_2022'].validate(bad))

    def test_controller_uses_exporter_and_is_whitelisted(self):
        # Exercise the real controller method without a bench/database/PDF toolkit.
        frappe = types.ModuleType('frappe')
        def whitelist():
            def decorate(method):
                method.is_whitelisted_for_test = True
                return method
            return decorate
        frappe.whitelist = whitelist
        frappe._ = lambda text: text
        frappe.get_value = lambda *args: '12.345.6789'
        frappe.render_template = lambda path, data: self.environment.get_template(path).render(data)
        def throw(message):
            raise ValueError(message)
        frappe.throw = throw
        model = types.ModuleType('frappe.model.document')
        model.Document = object
        utils = types.ModuleType('frappe.utils')
        utils.get_bench_path = lambda: ''
        modules = {'frappe': frappe, 'frappe.model.document': model,
                   'frappe.utils': utils, 'pypdftk': types.ModuleType('pypdftk')}
        with patch.dict(sys.modules, modules):
            spec = importlib.util.spec_from_file_location('u30_controller_test', DOCTYPE / 'at_vat_declaration.py')
            controller = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(controller)
            method = controller.ATVATDeclaration.generate_transfer_file
            self.assertTrue(method.is_whitelisted_for_test)
            result = method(self.document(tax_057=12))
            self.schemas['01_2022'].assertValid(etree.fromstring(result['content'].encode('utf-8')))
            with self.assertRaisesRegex(ValueError, 'July 2026'):
                method(self.document(amount_124=1))


if __name__ == '__main__':
    unittest.main()
