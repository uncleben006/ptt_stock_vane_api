from django.urls import path
from . import views

urlpatterns = [
    path("paragraphs/", views.PttStockParagraphsCreate.as_view(), name="ptt_stock_paragraphs_list_create"),
    path("paragraphs/edit/<int:id>/", views.PttStockParagraphsRetrieveUpdateDestroy.as_view(), name="ptt_stock_paragraphs_retrieve_update_destroy"),
    path("setting/", views.PttStockSettingListCreate.as_view(), name="ptt_stock_setting_list_create"),
    path("setting/edit/<int:id>/", views.PttStockSettingRetrieveUpdateDestroy.as_view(), name="ptt_stock_setting_retrieve_update_destroy"),
    path("targets/", views.PttStockTargetsListCreate.as_view(), name="ptt_stock_targets_list_create"),
    path("targets/edit/<int:id>/", views.PttStockTargetsRetrieveUpdateDestroy.as_view(), name="ptt_stock_targets_retrieve_update_destroy"),
    path("callback/", views.LineBotCallback.as_view(), name="line_bot_callback"),
]