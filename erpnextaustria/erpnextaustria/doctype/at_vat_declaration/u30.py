# -*- coding: utf-8 -*-
# Copyright (c) 2026, libracore and contributors
# For license information, please see license.txt

from calendar import monthrange
from datetime import datetime
from decimal import Decimal


SCHEMA_URLS = {
    '01_2022': 'https://www.bmf.gv.at/dam/jcr:5deafd50-12d6-4ac3-a9f7-0e234c690db2/BMF_ERKLAERUNGS_UEBERMITTLUNG_U30_01_2022.xsd',
    '07_2026': 'https://www.bmf.gv.at/dam/jcr:2e90eb5d-ef76-48a8-922b-dbf62cc2f230/BMF_ERKLAERUNGS_UEBERMITTLUNG_U30_07_2026.xsd'
}

# Order follows the BMF XSD sequences, not the numerical order of the KZ.
FIELDS = {
    'revenue_fields': [('000', 'revenue'), ('001', 'self_consumption'), ('021', 'receiver_vat')],
    'tax_free_fields': [
        ('011', 'exports'), ('012', 'subcontracting'), ('015', 'cross_border'),
        ('017', 'inner_eu'), ('018', 'vehicles_without_uid'), ('019', 'property_revenue'),
        ('016', 'small_businesses')
    ],
    'taxed_fields': [
        ('022', 'amount_normal'), ('124', 'amount_124'), ('029', 'reduced_amount'),
        ('006', 'reduced_amount_2'), ('037', 'reduced_amount_3'),
        ('052', 'amount_additional_1'), ('007', 'amount_additional_2'),
        ('056', 'tax_056'), ('057', 'tax_057'), ('048', 'tax_048'),
        ('044', 'tax_044'), ('032', 'tax_032')
    ],
    'acquisition_fields': [('070', 'intercommunal_revenue'), ('071', 'taxfree_intercommunal')],
    'taxed_acquisition_fields': [
        ('072', 'amount_inter_normal'), ('125', 'amount_125'),
        ('073', 'amount_inter_reduced_1'), ('008', 'amount_inter_reduced_2'),
        ('088', 'amount_inter_reduced_3'), ('076', 'external_taxation'), ('077', 'internal_taxation')
    ],
    'input_tax_fields': [
        ('060', 'total_pretax'), ('061', 'import_pretax'), ('083', 'import_charge_pretax'),
        ('065', 'intercommunal_pretax'), ('066', 'taxation_pretax'),
        ('082', 'taxation_building_pretax'), ('087', 'taxation_pretax_other_1'),
        ('089', 'taxation_pretax_other_2'), ('064', 'vehicles_pretax'),
        ('062', 'non_deductable_pretax'), ('063', 'corrections_1'),
        ('067', 'corrections_2'), ('090', 'tax_other_corrections')
    ]
}

# Preserve the field set and zero-valued elements of the original export before
# January 2022; the newer schemas must not be applied to historical periods.
LEGACY_FIELDS = (
    'revenue', 'exports', 'inner_eu', 'receiver_vat', 'amount_normal',
    'reduced_amount', 'tax_057', 'total_pretax', 'import_pretax',
    'import_charge_pretax', 'intercommunal_pretax', 'taxation_pretax',
    'intercommunal_revenue', 'amount_inter_normal'
)


def get_schema_version(start_date, end_date):
    start = datetime.strptime(str(start_date)[:10], '%Y-%m-%d').date()
    end = datetime.strptime(str(end_date)[:10], '%Y-%m-%d').date()
    if start <= end and end.year < 2022:
        # The original exporter did not require complete months or quarters.
        return 'legacy'
    same_month = start.year == end.year and start.month == end.month
    quarter = (start.year == end.year and start.month in (1, 4, 7, 10)
               and end.month == start.month + 2)
    if (start.day != 1 or end.day != monthrange(end.year, end.month)[1]
            or not (same_month or quarter)):
        raise ValueError('U30 requires a complete calendar month or quarter.')
    return '07_2026' if (start.year, start.month) >= (2026, 7) else '01_2022'


def get_amount(doc, field):
    return '{:.2f}'.format(Decimal(str(doc.get(field) or 0)))


def get_transfer_data(doc, fastnr, now):
    version = get_schema_version(doc.start_date, doc.end_date)
    data = {
        'schema_url': SCHEMA_URLS.get(version),
        'fastnr': fastnr.replace('.', ''),
        'datum': now.strftime('%Y-%m-%d'),
        'zeit': now.strftime('%H:%M:%S'),
        'von': str(doc.start_date)[:7],
        'bis': str(doc.end_date)[:7],
        'kundeninfo': doc.company
    }
    if version != '07_2026' and any(
            Decimal(get_amount(doc, field)) != 0 for field in ('amount_124', 'amount_125')):
        raise ValueError('KZ124 and KZ125 are only permitted from July 2026 onwards.')
    if version == 'legacy':
        # Keep the original numeric formatting (including float rounding).
        data.update((field, doc.get(field) or 0) for field in LEGACY_FIELDS)
        return data
    # BMF business checks require the section 6 exemption reason (VST) with
    # KZ020. The DocType has no such field, so do not emit an incomplete return.
    if Decimal(get_amount(doc, 'tax_free_revenue')) != 0:
        raise ValueError('KZ020 requires VST (the exemption reason under section 6(1)), '
                         'which this export does not support.')
    for group, fields in FIELDS.items():
        data[group] = []
        for code, field in fields:
            value = get_amount(doc, field)
            # Test the serialized amount: e.g. 0.004 must not produce an optional 0.00.
            if code != '000' and Decimal(value) == 0:
                continue
            data[group].append(('KZ' + code, value))
    return data
