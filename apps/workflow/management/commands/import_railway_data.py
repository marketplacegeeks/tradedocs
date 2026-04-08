"""
Simpler management command to import Railway data using Django's loaddata-like approach.
Usage: python manage.py import_railway_data
"""
import subprocess
from pathlib import Path
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Import data from railway_exports using Django dumpdata format'

    def handle(self, *args, **options):
        csv_dir = Path('railway_exports')

        # Use PostgreSQL COPY command for speed
        self.stdout.write(self.style.SUCCESS('Importing data from railway_exports...'))

        # Simple approach - use Django's loaddata if JSON dumps exist
        # Otherwise, use psql COPY commands for CSVs

        tables = [
            ('organisations', 'master_data_organisation'),
            ('organisation_tags', 'master_data_organisationtag'),
            ('organisation_addresses', 'master_data_organisationaddress'),
            ('banks', 'bank'),
            ('proforma_invoices', 'proforma_invoice'),
            ('proforma_invoice_line_items', 'proforma_invoice_line_item'),
            ('proforma_invoice_charges', 'proforma_invoice_charge'),
            ('packing_lists', 'packing_list'),
            ('containers', 'container'),
            ('container_items', 'container_item'),
            ('commercial_invoices', 'commercial_invoice'),
            ('commercial_invoice_line_items', 'commercial_invoice_line_item'),
        ]

        # For now, just print instructions for manual import
        self.stdout.write(self.style.WARNING(
            '\nManual import required. Run these SQL commands:\n'
        ))

        for csv_name, table_name in tables:
            csv_file = csv_dir / f'{csv_name}.csv'
            if csv_file.exists():
                self.stdout.write(f"\\COPY {table_name} FROM '{csv_file.absolute()}' CSV HEADER;")
