from django.core.management.base import BaseCommand
from ptt_stock_crawler.services.embed_stock_targets import embed_stock_targets

class Command(BaseCommand):
    help = 'Call GPT embed API and embed stock targets to Qdrant.'

    def handle(self, *args, **kwargs):
        embed_stock_targets()