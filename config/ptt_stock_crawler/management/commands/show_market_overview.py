from django.core.management.base import BaseCommand
from ptt_stock_crawler.services.show_market_overview import show_market_overview

class Command(BaseCommand):
    help = 'Show market overview'

    def handle(self, *args, **kwargs):
        
        show_market_overview()