from django.core.management.base import BaseCommand
from ptt_stock_crawler.services.analyze_stock_comments import analyze_stock_comments

class Command(BaseCommand):
    help = 'Call GPT API to analyze every comment\'s stock sentiment and stock target.'

    def handle(self, *args, **kwargs):
        analyze_stock_comments()