import json
from django.http import JsonResponse

from ...dbs.calendarEvent import *

from ..customers.update_customers import *

def extract_request_body(request):
    try:
        return json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

def handle_get_customer_data(data):

    customer_id = data.get('customerId')
    shop = data.get('shop')

    shop = "247c21-78.myshopify.com"

    session = shopify.Session(shop, "unstable", "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") #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
    shopify.ShopifyResource.activate_session(session)#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
    
    return JsonResponse(get_calendar_events_for_customer(customer_id, shop))

def handle_add_customer_product_to_calendar(data):

    customer_id = data.get('customerId')
    shop = data.get('shop')
    product_id = data.get('productId')
    date = data.get('date')

    shop = "247c21-78.myshopify.com"

    session = shopify.Session(shop, "unstable", "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")
    shopify.ShopifyResource.activate_session(session)

    r = add_calendar_event_for_customer(customer_id, product_id, shop, date)

    if not r:
        return JsonResponse({"status":"success"})
    else:
        return JsonResponse({"status":r})
        
def handle_remove_customer_product_from_calendar(data):

    customer_id = data.get('customerId')
    shop = data.get('shop')
    product_id = data.get('productId')
    date = data.get('date')

    shop = "247c21-78.myshopify.com"

    session = shopify.Session(shop, "unstable", "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")
    shopify.ShopifyResource.activate_session(session)

    return JsonResponse(remove_calendar_event_for_customer(customer_id, product_id, shop, date))

def handle_change_customer_product_date(data):

    customer_id = data.get('customerId')
    shop = data.get('shop')
    product_id = data.get('productId')
    date = data.get('date')

    shop = "247c21-78.myshopify.com"

    return JsonResponse(update_calendar_event_date_for_customer(customer_id, product_id, shop, date))

def handle_skip_number_of_months(data):
    
    customer_id = data.get('customerId')
    shop = data.get('shop')
    n = data.get('number_to_skip', 0)

    session = shopify.Session(shop, "unstable", "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")
    shopify.ShopifyResource.activate_session(session)
    r = customer_skip_months(customer_id, shop, n)

    return JsonResponse({'status': r})

def handle_case_each_month(data):
    
    customer_id = data.get('customerId')
    shop = data.get('shop')

    shop = "247c21-78.myshopify.com"

    session = shopify.Session(shop, "unstable", "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")
    shopify.ShopifyResource.activate_session(session)

    r = customer_case_each_month(customer_id)

    return JsonResponse({'status': r})

def handle_commited_months(data):

    customer_id = data.get('customerId')
    shop = data.get('shop')
    months = data.get('months')

    shop = "247c21-78.myshopify.com"

    session = shopify.Session(shop, "unstable", "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")
    shopify.ShopifyResource.activate_session(session)

    r = customer_commited_months(customer_id, months)

    return JsonResponse({'status': r})

def handle_products_per_month(data):

    customer_id = data.get('customerId')
    shop = data.get('shop')
    products = data.get('products')

    shop = "247c21-78.myshopify.com"
    
    session = shopify.Session(shop, "unstable", "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")
    shopify.ShopifyResource.activate_session(session)

    r = customer_products_per_month(customer_id, products)
    deal_with_product_change_calendar(customer_id, shop)

    return JsonResponse({'status': r})

def handle_sub_frequency(data):

    customer_id = data.get('customerId')
    shop = data.get('shop')
    frequency = data.get('frequency')

    shop = "247c21-78.myshopify.com"
    
    session = shopify.Session(shop, "unstable", "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")
    shopify.ShopifyResource.activate_session(session)

    r = customer_sub_frequency(customer_id, frequency)

    return JsonResponse({'status': r})

def handle_has_case_each_month(data):

    customer_id = data.get('customerId')
    shop = data.get('shop')

    shop = "247c21-78.myshopify.com"

    session = shopify.Session(shop, "unstable", "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")
    shopify.ShopifyResource.activate_session(session)

    r = get_customer_metafield(customer_id, "deet", "case_each_month")

    return JsonResponse({'status': r["value"]})

def handle_is_subscribed(data):

    customer_id = data.get('customerId')
    shop = data.get('shop')

    shop = "247c21-78.myshopify.com"

    session = shopify.Session(shop, "unstable", "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")
    shopify.ShopifyResource.activate_session(session)

    r = is_customer_subscribed(customer_id)
    #print("r: ",r)

    if r == False:
        return JsonResponse({'status': False})

    return JsonResponse({'status': True})

def handle_cancel_subscription(data):

    customer_id = data.get('customerId')
    shop = data.get('shop')

    session = shopify.Session(shop, "unstable", "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")
    shopify.ShopifyResource.activate_session(session)

    r = is_customer_subscribed(customer_id)

    if r == False:
        return JsonResponse({'status': 'user not subscribed'})
    
    else:
        cancel_subscription(r['id'])
        return JsonResponse({'status': 'cancelled'})
    
def handle_get_customer_deet_details(data):

    customer_id = data.get('customerId')
    shop = data.get('shop')

    shop = "247c21-78.myshopify.com"

    session = shopify.Session(shop, "unstable", "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")
    shopify.ShopifyResource.activate_session(session)

    subbed = is_customer_subscribed(customer_id)
    skippped_months = get_customer_metafield(customer_id, "deet", "skipped_months")
    calendar_skipped = get_customer_metafield(customer_id, "deet", "calendar_skipped")
    products_per_month = get_customer_metafield(customer_id, "deet", "products_per_month")
    commited_months = get_customer_metafield(customer_id, "deet", "commited_months")
    sub_frequency = get_customer_metafield(customer_id, "deet", "sub_frequency")
    case_each_month = get_customer_metafield(customer_id, "deet", "case_each_month")

    return_data = {
        "subbed":subbed,
        "skippped_months": float(skippped_months["value"]) if skippped_months else None,
        "calendar_skipped": bool(calendar_skipped["value"]) if calendar_skipped else None,
        "products_per_month":float(products_per_month["value"]) if products_per_month else None,
        "commited_months": float(products_per_month["value"]) if commited_months else None,
        "sub_frequency": float(sub_frequency["value"]) if sub_frequency else None,
        "case_each_month":bool(case_each_month["value"]) if case_each_month else None
    }

    print("return_data: ",return_data)

    return JsonResponse(return_data)

def handle_get_customers_next_scent(data):

    customer_id = data.get('customerId')
    shop = data.get('shop')

    shop = "247c21-78.myshopify.com"

    session = shopify.Session(shop, "unstable", "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")
    shopify.ShopifyResource.activate_session(session)

    return JsonResponse(fetch_event_details(get_most_recent_future_event(customer_id, shop)))




