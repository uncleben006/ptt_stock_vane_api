from django.core.management.base import BaseCommand
from ptt_stock_crawler.services.analyze_stock_comments import analyze_stock_comments

class Command(BaseCommand):
    help = 'Segment the comments and use Levenshtein distance to search for words similar to those in the stock dictionary. Finally, let GPT determine whether the comment mentions a company.'

    def handle(self, *args, **kwargs):
        analyze_stock_comments()