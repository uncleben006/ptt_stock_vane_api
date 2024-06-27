from django.core.management.base import BaseCommand
from ptt_stock_crawler.services.update_stock_paragraphs import fetch_and_update_stock_paragraphs

class Command(BaseCommand):
    help = 'Fetches stock paragraphs from PTT stock forum and inserts them into the database'

    def handle(self, *args, **kwargs):
        fetch_and_update_stock_paragraphs()