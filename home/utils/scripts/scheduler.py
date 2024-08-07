import os

import schedule
import shopify
import time
from datetime import datetime, timedelta
from django.utils import timezone

from home.models import FailedSubscriptionAttempt
from home.settings import * 

from ..shopify.subscriptions.update_subs import *

def retry_failed_payments():
    print(f"Running scheduled task at {datetime.now()}")

    attempts = FailedSubscriptionAttempt.objects.filter(
        status='pending',
        next_retry__lte=timezone.now()
    )

    for attempt in attempts:

        sub_id = attempt.subscription_id

        if attempt.retry_count >= MAX_RETRIES:

            attempt.status = 'failed'
            attempt.save()

            customer_id = get_sub_contract_customer(sub_id)

            freq = get_customer_metafield(customer_id, "deet", "sub_frequency")
            freq = freq if freq else {"value":1}

            skipped = get_customer_metafield(customer_id, "deet", "skipped_months")
            skipped = skipped if skipped else {"value":1}

            today = datetime.today()
            if today.month == 12: 

                if float(freq["value"]) > 1:
                    next_month = 1 + float(freq["value"]) + float(skipped["value"])
                else:
                    next_month = 1 + float(skipped["value"])

                year = today.year + 1
            else:

                if float(freq["value"]) > 1:
                    next_month = today.month + 1 + float(freq["value"]) + float(skipped["value"])
                else:
                    next_month = today.month + 1 + float(skipped["value"])

                year = today.year

            next_billing_date = datetime(year, int(next_month), 10)
            print("next_billing_date: ",next_billing_date)
            set_next_billing_date(sub_id, next_billing_date)
                    
            continue
        
        # Your retry logic here
        print(f"Retrying payment for subscription ID: {sub_id}")

        success = retry_payment_via_shopify(sub_id)

        if success:
            attempt.status = 'success'
        else:
            attempt.schedule_next_retry()

def retry_payment_via_shopify(request, subsrciption_id):

    def find_next_unbilled_not_skipped_cycle(billing_cycles):
        for cycle in billing_cycles:
            node = cycle['node']
            if node['status'] == 'UNBILLED' and not node['skipped']:
                return node
        return None

    session = shopify.Session("247c21-78.myshopify.com", "unstable", "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") #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
    shopify.ShopifyResource.activate_session(session)

    billing_cycles = get_billing_cycles(subsrciption_id)
    next_bill = find_next_unbilled_not_skipped_cycle(billing_cycles)

    if next_bill:

        next_bill['cycleStartAt'] = datetime.strptime(next_bill['cycleStartAt'], "%Y-%m-%dT%H:%M:%SZ")
        create_subscription_billing_attempt(subsrciption_id, next_bill['cycleIndex'], next_bill['cycleStartAt'])
    
# Schedule the task
schedule.every(1).minutes.do(retry_failed_payments)

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(1)