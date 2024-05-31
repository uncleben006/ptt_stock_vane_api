from django.core.management.base import BaseCommand
from ptt_stock_crawler.services.update_ptt_stock_sentiments import update_stock_sentiments

class Command(BaseCommand):
    help = 'Call GPT API to analyze every comment\'s stock sentiment and inserts them into the database'

    def handle(self, *args, **kwargs):
        update_stock_sentiments()