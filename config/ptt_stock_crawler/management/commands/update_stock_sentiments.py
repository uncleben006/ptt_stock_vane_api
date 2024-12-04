from django.core.management.base import BaseCommand
from ptt_stock_crawler.services.update_stock_sentiment import update_stock_sentiment

class Command(BaseCommand):
    help = 'Analyze stock sentiment using assistants api with gpt-4o-mini'

    def handle(self, *args, **kwargs):
        update_stock_sentiment()