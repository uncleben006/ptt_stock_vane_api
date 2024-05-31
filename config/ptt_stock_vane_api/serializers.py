from rest_framework import serializers
from .models import PttStockParagraphs, PttStockSetting, PttStockTargets

class PttStockParagraphsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PttStockParagraphs
        fields = '__all__'

class PttStockSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PttStockSetting
        fields = '__all__'

class PttStockTargetsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PttStockTargets
        fields = '__all__'