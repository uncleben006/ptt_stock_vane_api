from django.core.management.base import BaseCommand
from ptt_stock_crawler.services.update_stock_targets import fetch_and_insert_stock_targets

class Command(BaseCommand):
    help = 'Fetches stock targets from a remote API and inserts them into the database'

    def handle(self, *args, **kwargs):
        fetch_and_insert_stock_targets()