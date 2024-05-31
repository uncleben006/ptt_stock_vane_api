from django.db import models

# Create your models here.
class PttStockParagraphs(models.Model):
    paragraph_link = models.CharField(max_length=255)
    paragraph_author = models.CharField(max_length=255)
    paragraph_title = models.CharField(max_length=255)
    paragraph_published_time = models.DateTimeField()
    paragraph_content = models.TextField()
    paragraph_ip = models.CharField(max_length=32)
    paragraph_country = models.CharField(max_length=32)
    comments = models.JSONField()
    status = models.CharField(max_length=8)
    md5_hash = models.CharField(max_length=255)
    paragraph_content_token_count = models.IntegerField()
    comments_token_count = models.IntegerField()
    paragraph_tag = models.CharField(max_length=32)
    paragraph_stock_targets = models.JSONField()
    page_url = models.CharField(max_length=255, default="https://www.ptt.cc/bbs/Stock/index.html")

    def __str__(self):
        return self.paragraph_title

    class Meta:
        db_table = "ptt_stock_paragraphs"

class PttStockSetting(models.Model):
    setting = models.CharField(max_length=64)
    value = models.IntegerField()

    def __str__(self):
        return self.setting

    class Meta:
        db_table = "ptt_stock_setting"

class PttStockTargets(models.Model):
    no = models.CharField(max_length=16, null=False, unique=True)
    name = models.CharField(max_length=64, null=True)

    def __str__(self):
        return self.no +' '+ self.name    

    class Meta:
        db_table = "ptt_stock_targets"