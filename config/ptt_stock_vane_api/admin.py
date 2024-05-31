from django.contrib import admin
from .models import PttStockParagraphs, PttStockSetting, PttStockTargets

# Register your models here.
admin.site.register(PttStockParagraphs)
admin.site.register(PttStockSetting)
admin.site.register(PttStockTargets)
