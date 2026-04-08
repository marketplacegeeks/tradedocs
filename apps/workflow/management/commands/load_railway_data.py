"""
Management command to load data from Railway export CSVs into local database.
Usage: python manage.py load_railway_data
"""
import csv
from decimal import Decimal
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.master_data.models import Organisation, OrganisationAddress, OrganisationTag, Bank
from apps.proforma_invoice.models import ProformaInvoice, ProformaInvoiceLineItem, ProformaInvoiceCharge
from apps.packing_list.models import PackingList, Container, ContainerItem
from apps.commercial_invoice.models import CommercialInvoice, CommercialInvoiceLineItem


class Command(BaseCommand):
    help = 'Load data from railway_exports CSV files into local database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dir',
            type=str,
            default='railway_exports',
            help='Directory containing the CSV files',
        )

    def handle(self, *args, **options):
        csv_dir = Path(options['dir'])
        if not csv_dir.exists():
            self.stderr.write(self.style.ERROR(f'Directory not found: {csv_dir}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Loading data from {csv_dir}...'))

        with transaction.atomic():
            # Order matters - load in dependency order
            self.load_organisations(csv_dir / 'organisations.csv')
            self.load_organisation_tags(csv_dir / 'organisation_tags.csv')
            self.load_organisation_addresses(csv_dir / 'organisation_addresses.csv')
            self.load_banks(csv_dir / 'banks.csv')
            self.load_proforma_invoices(csv_dir / 'proforma_invoices.csv')
            self.load_proforma_invoice_line_items(csv_dir / 'proforma_invoice_line_items.csv')
            self.load_proforma_invoice_charges(csv_dir / 'proforma_invoice_charges.csv')
            self.load_packing_lists(csv_dir / 'packing_lists.csv')
            self.load_containers(csv_dir / 'containers.csv')
            self.load_container_items(csv_dir / 'container_items.csv')
            self.load_commercial_invoices(csv_dir / 'commercial_invoices.csv')
            self.load_commercial_invoice_line_items(csv_dir / 'commercial_invoice_line_items.csv')

        self.stdout.write(self.style.SUCCESS('✓ All data loaded successfully'))

    def load_organisations(self, path):
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'Skipping {path.name} (not found)'))
            return

        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                Organisation.objects.update_or_create(
                    id=int(row['id']),
                    defaults={
                        'name': row['name'],
                        'is_active': row['is_active'] == 't',
                    }
                )
                count += 1
        self.stdout.write(f'  ✓ Loaded {count} organisations')

    def load_organisation_tags(self, path):
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'Skipping {path.name} (not found)'))
            return

        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                OrganisationTag.objects.update_or_create(
                    id=int(row['id']),
                    defaults={
                        'organisation_id': int(row['organisation_id']),
                        'tag': row['tag'],
                    }
                )
                count += 1
        self.stdout.write(f'  ✓ Loaded {count} organisation tags')

    def load_organisation_addresses(self, path):
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'Skipping {path.name} (not found)'))
            return

        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                OrganisationAddress.objects.update_or_create(
                    id=int(row['id']),
                    defaults={
                        'organisation_id': int(row['organisation_id']),
                        'address_type': row['address_type'],
                        'line1': row['line1'],
                        'line2': row['line2'] or '',
                        'city': row['city'],
                        'state': row['state'],
                        'pin': row['pin'],
                        'country_id': int(row['country_id']) if row['country_id'] else None,
                        'phone_country_code': row['phone_country_code'] or '',
                        'phone_number': row['phone_number'] or '',
                        'email': row['email'] or '',
                        'contact_name': row['contact_name'] or '',
                        'iec_code': row['iec_code'] or '',
                        'tax_type': row['tax_type'] or '',
                        'tax_code': row['tax_code'] or '',
                    }
                )
                count += 1
        self.stdout.write(f'  ✓ Loaded {count} organisation addresses')

    def load_banks(self, path):
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'Skipping {path.name} (not found)'))
            return

        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                Bank.objects.update_or_create(
                    id=int(row['id']),
                    defaults={
                        'beneficiary_name': row['beneficiary_name'],
                        'bank_name': row['bank_name'],
                        'branch': row['branch'] or '',
                        'account_number': row['account_number'],
                        'account_type': row['account_type'],
                        'swift_code': row['swift_code'] or '',
                        'iban': row['iban'] or '',
                        'ifsc_code': row['ifsc_code'] or '',
                        'routing_number': row['routing_number'] or '',
                        'currency_id': int(row['currency_id']),
                        'is_active': row['is_active'] == 't',
                    }
                )
                count += 1
        self.stdout.write(f'  ✓ Loaded {count} banks')

    def load_proforma_invoices(self, path):
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'Skipping {path.name} (not found)'))
            return

        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                # Handle nullable foreign keys
                def get_fk(key):
                    return int(row[key]) if row[key] and row[key] != '' else None

                def get_decimal(key):
                    return Decimal(row[key]) if row[key] and row[key] != '' else None

                ProformaInvoice.objects.update_or_create(
                    id=int(row['id']),
                    defaults={
                        'pi_number': row['pi_number'],
                        'pi_date': row['pi_date'],
                        'buyer_order_no': row['buyer_order_no'] or '',
                        'buyer_order_date': row['buyer_order_date'] or None,
                        'other_references': row['other_references'] or '',
                        'vessel_flight_no': row['vessel_flight_no'] or '',
                        'validity_for_acceptance': row['validity_for_acceptance'] or '',
                        'validity_for_shipment': row['validity_for_shipment'] or '',
                        'partial_shipment': row['partial_shipment'] or '',
                        'transshipment': row['transshipment'] or '',
                        'tc_content': row['tc_content'] or '',
                        'freight': get_decimal('freight'),
                        'insurance_amount': get_decimal('insurance_amount'),
                        'import_duty': get_decimal('import_duty'),
                        'destination_charges': get_decimal('destination_charges'),
                        'status': row['status'],
                        'bank_id': get_fk('bank_id'),
                        'buyer_id': get_fk('buyer_id'),
                        'consignee_id': get_fk('consignee_id'),
                        'country_of_final_destination_id': get_fk('country_of_final_destination_id'),
                        'country_of_origin_id': get_fk('country_of_origin_id'),
                        'created_by_id': get_fk('created_by_id'),
                        'exporter_id': get_fk('exporter_id'),
                        'final_destination_id': get_fk('final_destination_id'),
                        'incoterms_id': get_fk('incoterms_id'),
                        'payment_terms_id': get_fk('payment_terms_id'),
                        'place_of_receipt_id': get_fk('place_of_receipt_id'),
                        'port_of_discharge_id': get_fk('port_of_discharge_id'),
                        'port_of_loading_id': get_fk('port_of_loading_id'),
                        'pre_carriage_by_id': get_fk('pre_carriage_by_id'),
                        'tc_template_id': get_fk('tc_template_id'),
                        'place_of_receipt_by_pre_carrier_id': get_fk('place_of_receipt_by_pre_carrier_id'),
                        'bank_charges_to_buyer': row.get('bank_charges_to_buyer', 'f') == 't',
                    }
                )
                count += 1
        self.stdout.write(f'  ✓ Loaded {count} proforma invoices')

    def load_proforma_invoice_line_items(self, path):
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'Skipping {path.name} (not found)'))
            return

        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                def get_fk(key):
                    return int(row[key]) if row[key] and row[key] != '' else None

                def get_decimal(key):
                    return Decimal(row[key]) if row[key] and row[key] != '' else Decimal('0')

                ProformaInvoiceLineItem.objects.update_or_create(
                    id=int(row['id']),
                    defaults={
                        'proforma_invoice_id': int(row['proforma_invoice_id']),
                        'hsn_code': row['hsn_code'] or '',
                        'item_code': row['item_code'],
                        'description': row['description'],
                        'quantity': get_decimal('quantity'),
                        'rate': get_decimal('rate'),
                        'amount': get_decimal('amount'),
                        'uom_id': get_fk('uom_id'),
                    }
                )
                count += 1
        self.stdout.write(f'  ✓ Loaded {count} PI line items')

    def load_proforma_invoice_charges(self, path):
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'Skipping {path.name} (not found)'))
            return

        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                ProformaInvoiceCharge.objects.update_or_create(
                    id=int(row['id']),
                    defaults={
                        'proforma_invoice_id': int(row['proforma_invoice_id']),
                        'charge_name': row['charge_name'],
                        'amount': Decimal(row['amount']),
                    }
                )
                count += 1
        self.stdout.write(f'  ✓ Loaded {count} PI charges')

    def load_packing_lists(self, path):
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'Skipping {path.name} (not found)'))
            return

        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                def get_fk(key):
                    return int(row[key]) if row[key] and row[key] != '' else None

                PackingList.objects.update_or_create(
                    id=int(row['id']),
                    defaults={
                        'pl_number': row['pl_number'],
                        'pl_date': row['pl_date'],
                        'proforma_invoice_id': int(row['proforma_invoice_id']),
                        'exporter_id': int(row['exporter_id']),
                        'consignee_id': int(row['consignee_id']),
                        'buyer_id': get_fk('buyer_id'),
                        'notify_party_id': get_fk('notify_party_id'),
                        'pre_carriage_by_id': get_fk('pre_carriage_by_id'),
                        'place_of_receipt_id': get_fk('place_of_receipt_id'),
                        'place_of_receipt_by_pre_carrier_id': get_fk('place_of_receipt_by_pre_carrier_id'),
                        'vessel_flight_no': row['vessel_flight_no'] or '',
                        'port_of_loading_id': get_fk('port_of_loading_id'),
                        'port_of_discharge_id': get_fk('port_of_discharge_id'),
                        'final_destination_id': get_fk('final_destination_id'),
                        'country_of_origin_id': get_fk('country_of_origin_id'),
                        'country_of_final_destination_id': get_fk('country_of_final_destination_id'),
                        'po_number': row['po_number'] or '',
                        'po_date': row['po_date'] or None,
                        'lc_number': row['lc_number'] or '',
                        'lc_date': row['lc_date'] or None,
                        'bl_number': row['bl_number'] or '',
                        'bl_date': row['bl_date'] or None,
                        'so_number': row['so_number'] or '',
                        'so_date': row['so_date'] or None,
                        'other_references': row['other_references'] or '',
                        'other_references_date': row['other_references_date'] or None,
                        'additional_description': row['additional_description'] or '',
                        'incoterms_id': get_fk('incoterms_id'),
                        'payment_terms_id': get_fk('payment_terms_id'),
                        'status': row['status'],
                        'created_by_id': int(row['created_by_id']),
                    }
                )
                count += 1
        self.stdout.write(f'  ✓ Loaded {count} packing lists')

    def load_containers(self, path):
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'Skipping {path.name} (not found)'))
            return

        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                Container.objects.update_or_create(
                    id=int(row['id']),
                    defaults={
                        'packing_list_id': int(row['packing_list_id']),
                        'container_ref': row['container_ref'],
                        'marks_numbers': row['marks_numbers'],
                        'seal_number': row['seal_number'],
                        'tare_weight': Decimal(row['tare_weight']),
                        'gross_weight': Decimal(row['gross_weight']),
                    }
                )
                count += 1
        self.stdout.write(f'  ✓ Loaded {count} containers')

    def load_container_items(self, path):
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'Skipping {path.name} (not found)'))
            return

        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                ContainerItem.objects.update_or_create(
                    id=int(row['id']),
                    defaults={
                        'container_id': int(row['container_id']),
                        'hsn_code': row['hsn_code'] or '',
                        'item_code': row['item_code'],
                        'description': row['description'],
                        'batch_details': row['batch_details'] or '',
                        'uom_id': int(row['uom_id']),
                        'type_of_package_id': int(row['type_of_package_id']),
                        'no_of_packages': Decimal(row['no_of_packages']),
                        'qty_per_package': Decimal(row['qty_per_package']),
                        'weight_per_unit_packaging': Decimal(row['weight_per_unit_packaging']),
                        'net_material_weight': Decimal(row['net_material_weight']),
                        'item_gross_weight': Decimal(row['item_gross_weight']),
                    }
                )
                count += 1
        self.stdout.write(f'  ✓ Loaded {count} container items')

    def load_commercial_invoices(self, path):
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'Skipping {path.name} (not found)'))
            return

        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                def get_fk(key):
                    return int(row[key]) if row[key] and row[key] != '' else None

                def get_decimal(key):
                    return Decimal(row[key]) if row[key] and row[key] != '' else None

                CommercialInvoice.objects.update_or_create(
                    id=int(row['id']),
                    defaults={
                        'ci_number': row['ci_number'],
                        'packing_list_id': int(row['packing_list_id']),
                        'bank_id': get_fk('bank_id'),
                        'freight': get_decimal('freight'),
                        'insurance_amount': get_decimal('insurance_amount'),
                        'bank_charges_to_buyer': row.get('bank_charges_to_buyer', 'f') == 't',
                    }
                )
                count += 1
        self.stdout.write(f'  ✓ Loaded {count} commercial invoices')

    def load_commercial_invoice_line_items(self, path):
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'Skipping {path.name} (not found)'))
            return

        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                CommercialInvoiceLineItem.objects.update_or_create(
                    id=int(row['id']),
                    defaults={
                        'commercial_invoice_id': int(row['commercial_invoice_id']),
                        'item_code': row['item_code'],
                        'description': row['description'],
                        'total_quantity': Decimal(row['total_quantity']),
                        'rate': Decimal(row['rate']),
                        'amount': Decimal(row['amount']),
                        'uom_id': int(row['uom_id']),
                    }
                )
                count += 1
        self.stdout.write(f'  ✓ Loaded {count} CI line items')
