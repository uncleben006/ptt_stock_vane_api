from django.shortcuts import render
from .services.update_ptt_name_id import fetch_and_insert_stock_targets

# Create your views here.
def fetch_and_insert_stock_targets_view(request):
    fetch_and_insert_stock_targets()
    return render(request, "ptt_stock_crawler/stock_targets.html")