from django.db import models
from .settings import *
from django.utils import timezone

class CalendarEvent(models.Model):
    
    shopify_product_id = models.CharField(max_length=100)
    event_date = models.DateField()
    shopify_customer_id = models.CharField(max_length=100)
    shopify_shop_domain = models.CharField(max_length=255)

    def __str__(self):
        return f"Product {self.shopify_product_id} on {self.event_date} for customer {self.shopify_customer_id} from shop {self.shopify_shop_domain}"

class FailedSubscriptionAttempt(models.Model):
    subscription_id = models.CharField(max_length=255)
    retry_count = models.IntegerField(default=0)
    last_attempt = models.DateTimeField(auto_now_add=True)
    next_retry = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default='pending')

    def schedule_next_retry(self):
        self.retry_count += 1
        self.next_retry = timezone.now() + timezone.timedelta(minutes=RETRY_INTERVAL_MINUTES)
        self.save()

    def __str__(self):
        return f"Subscription ID: {self.subscription_id}, Retry Count: {self.retry_count}, Status: {self.status}"