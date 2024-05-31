import os, json, logging
from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import PttStockParagraphs, PttStockSetting, PttStockTargets
from .serializers import PttStockParagraphsSerializer, PttStockSettingSerializer, PttStockTargetsSerializer

from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, FollowEvent, UnfollowEvent, JoinEvent, PostbackEvent, MemberJoinedEvent, MemberLeftEvent, TextSendMessage

logger = logging.getLogger()
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
parser = WebhookParser(os.getenv("LINE_CHANNEL_SECRET"))

class PttStockParagraphsCreate(generics.ListCreateAPIView):
    queryset = PttStockParagraphs.objects.all()
    serializer_class = PttStockParagraphsSerializer

class PttStockParagraphsRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = PttStockParagraphs.objects.all()
    serializer_class = PttStockParagraphsSerializer
    lookup_field = "id"

class PttStockSettingListCreate(generics.ListCreateAPIView):
    queryset = PttStockSetting.objects.all()
    serializer_class = PttStockSettingSerializer

class PttStockSettingRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = PttStockSetting.objects.all()
    serializer_class = PttStockSettingSerializer
    lookup_field = "id"

class PttStockTargetsListCreate(generics.ListCreateAPIView):
    queryset = PttStockTargets.objects.all()
    serializer_class = PttStockTargetsSerializer
  
class PttStockTargetsRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = PttStockTargets.objects.all()
    serializer_class = PttStockTargetsSerializer
    lookup_field = "id"
class LineBotCallback(APIView):
    def post(self, request):
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')
        # logger.info(signature)
        # logger.info(body)
        # logger.info(json.dumps(request.data, indent=2))
        try:
            events = parser.parse(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()

        for event in events:
            logger.info(event)
            if isinstance(event, MessageEvent):
                mtext = event.message.text
                message = []
                message.append(TextSendMessage(text=mtext))
                line_bot_api.reply_message(event.reply_token, message)
            elif isinstance(event, FollowEvent):
                mtext = event.message.text
                message = []
                message.append(TextSendMessage(text=mtext))
                line_bot_api.reply_message(event.reply_token, message)
            elif isinstance(event, UnfollowEvent):
                mtext = event.message.text
                message = []
                message.append(TextSendMessage(text=mtext))
                line_bot_api.reply_message(event.reply_token, message)
            elif isinstance(event, JoinEvent):
                mtext = event.message.text
                message = []
                message.append(TextSendMessage(text=mtext))
                line_bot_api.reply_message(event.reply_token, message)
            elif isinstance(event, PostbackEvent):
                mtext = event.message.text
                message = []
                message.append(TextSendMessage(text=mtext))
                line_bot_api.reply_message(event.reply_token, message)
            elif isinstance(event, MemberJoinedEvent):
                mtext = event.message.text
                message = []
                message.append(TextSendMessage(text=mtext))
                line_bot_api.reply_message(event.reply_token, message)
            elif isinstance(event, MemberLeftEvent):
                mtext = event.message.text
                message = []
                message.append(TextSendMessage(text=mtext))
                line_bot_api.reply_message(event.reply_token, message)

        return Response(status=status.HTTP_200_OK)