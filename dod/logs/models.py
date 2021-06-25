from django.db import models


class MMSSendLog(models.Model):
    code = models.CharField(max_length=40)
    phone = models.CharField(max_length=30)
    item_name = models.CharField(max_length=100)
    item_url = models.URLField()
    due_date = models.CharField(max_length=30, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resend = models.BooleanField(default=False)
