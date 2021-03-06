from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection

from ...utils.random_data import (
    create_orders, create_users, create_shipping_methods,
    create_products_by_schema, create_product_sales, create_vouchers,
    create_groups, set_featured_products, add_address_to_admin)
from ...utils import create_superuser


class Command(BaseCommand):
    help = 'Populate database with test objects'
    placeholders_dir = r'saleor/static/placeholders/'

    def add_arguments(self, parser):
        parser.add_argument(
            '--createsuperuser',
            action='store_true',
            dest='createsuperuser',
            default=False,
            help='Create admin account')
        parser.add_argument(
            '--withoutimages',
            action='store_true',
            dest='withoutimages',
            default=False,
            help='Don\'t create product images')
        parser.add_argument(
            '--withoutsearch',
            action='store_true',
            dest='withoutsearch',
            default=False,
            help='Don\'t update search index')

    def make_database_faster(self):
        '''Sacrifices some of the safeguards of sqlite3 for speed

        Users are not likely to run this command in a production environment.
        They are even less likely to run it in production while using sqlite3.
        '''
        if 'sqlite3' in connection.settings_dict['ENGINE']:
            cursor = connection.cursor()
            cursor.execute('PRAGMA temp_store = MEMORY;')
            cursor.execute('PRAGMA synchronous = OFF;')

    def populate_search_index(self):
        if settings.ES_URL:
            call_command('search_index', '--rebuild', force=True)

    def handle(self, *args, **options):
        self.make_database_faster()
        create_images = not options['withoutimages']
        for msg in create_shipping_methods():
            self.stdout.write(msg)
        create_products_by_schema(self.placeholders_dir, 10, create_images,
                                  stdout=self.stdout)
        for msg in create_product_sales(5):
            self.stdout.write(msg)
        for msg in create_vouchers():
            self.stdout.write(msg)
        for msg in create_users(20):
            self.stdout.write(msg)
        for msg in create_orders(20):
            self.stdout.write(msg)
        for msg in set_featured_products(16):
            self.stdout.write(msg)
        self.stdout.write(create_groups())

        if options['createsuperuser']:
            credentials = {'email': 'admin@example.com', 'password': 'admin'}
            msg = create_superuser(credentials)
            self.stdout.write(msg)
            add_address_to_admin(credentials['email'])
        if not options['withoutsearch']:
            self.populate_search_index()
