from django.utils import timezone

from ...models import CalendarEvent

from ..shopify.general.customer import *

from ..shopify.products.get_products import *

from ..shopify.customers.get_customers import *

from datetime import datetime, date as dt_date

INTERVAL = "MONTH"

def add_months(original_date, months):
    month = original_date.month - 1 + months
    year = original_date.year + month // 12
    month = month % 12 + 1
    day = min(original_date.day, [31, 29 if year % 4 == 0 and not year % 100 == 0 or year % 400 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
    return original_date.replace(year=year, month=month, day=day)

def fetch_event_details(event):

    if event:
        premium_value = get_variants_premium_value(event.shopify_product_id)
        variant_info = get_product_variant_details(event.shopify_product_id)

        #print("variant_info: ",variant_info)

        if 'data' in variant_info and 'productVariant' in variant_info['data']:
            variant_info = variant_info['data']['productVariant']
        else:
            variant_info =  None

        name = "EMPTY"
        if variant_info:
            name = variant_info['displayName']

        imageURL = ""
        imageAlt = ""
        vendor = ""
        if variant_info:

            print(variant_info['image'])
            if variant_info['image']:
                if variant_info['image']['altText']:
                    imageAlt = variant_info['image']['altText']

                if variant_info['image']['url']:
                    imageURL = variant_info['image']['url']

            elif variant_info['product'] and variant_info['product']['featuredImage']:
                
                if variant_info['product']['featuredImage']['altText']:
                    imageAlt = variant_info['product']['featuredImage']['altText']

                if variant_info['product']['featuredImage']['url']:
                    imageURL = variant_info['product']['featuredImage']['url']

            if variant_info['product']:
                vendor  = variant_info['product']['vendor']
        
        return {
            "product_id": event.shopify_product_id,
            "premium_value":premium_value,
            "name":name,
            "vendor":vendor,
            "image_url":imageURL,
            "image_alt":imageAlt,
            "customer_id": event.shopify_customer_id,
            "shop": event.shopify_shop_domain,
            "date": event.event_date
        }
    
    else:
        return {}


def get_most_recent_future_event(customer_id:str, shop_domain):

    customer_id = str(customer_id)

    customer_id = customer_id.replace("gid://shopify/Customer/", "").strip()
    today = timezone.now().date()
    calendar_event = CalendarEvent.objects.filter(
        shopify_customer_id=customer_id,
        event_date__gt=today
        ).order_by("event_date")
    
    #print("get_most_recent_future_event: ",calendar_event)
    
    if calendar_event.exists():
        return calendar_event.first()
    else:
        return None
    
def get_most_recent_future_events(customer_id:str, shop_domain):

    customer_id = str(customer_id)

    customer_id = customer_id.replace("gid://shopify/Customer/", "").strip()
    today = timezone.now().date()
    calendar_event = CalendarEvent.objects.filter(
        shopify_customer_id=customer_id,
        event_date__gt=today
        ).order_by("event_date")
    
    #print("get_most_recent_future_event: ",calendar_event)
    
    if calendar_event.exists():
        return calendar_event
    else:
        return None

def get_calendar_events_for_customer(customer_id, shop):

    events = CalendarEvent.objects.filter(shopify_customer_id=customer_id, shopify_shop_domain=shop).order_by("event_date")
    event_details = [fetch_event_details(event) for event in events]

    return {'event_details': event_details}

def count_products_in_month_for_customer(customer_id, shop, date):

    try:
        event_date = datetime.strptime(date, '%Y-%m-%d').date()
    except:
        event_date = date

    # Check for the number of records sharing the same month and year
    same_month_count = CalendarEvent.objects.filter(
        shopify_customer_id=customer_id,
        shopify_shop_domain=shop,
        event_date__year=event_date.year,
        event_date__month=event_date.month
    ).count()

    return same_month_count

def check_product_for_month(customer_id, product_id, shop, date):

    try:
        event_date = datetime.strptime(date, '%Y-%m-%d').date()
    except:
        event_date = date

    # Check for the number of records sharing the same month and year
    same_month_count = CalendarEvent.objects.filter(
        shopify_customer_id=customer_id,
        shopify_shop_domain=shop,
        event_date__year=event_date.year,
        event_date__month=event_date.month,
        shopify_product_id=product_id,
    ).count()

    return True if same_month_count > 0 else False


def add_calendar_event_for_customer(customer_id, product_id, shop, date):

    def skipped_month_sub_freq_deal(date, customer_id):

        from ..shopify.customers.update_customers import add_customer_metafield, update_customer_metafield

        return_date = date

        skipped_months = get_customer_metafield(customer_id, "deet", "skipped_months")
        calendar_skipped = get_customer_metafield(customer_id, "deet", "calendar_skipped")

        sub_freq = get_customer_metafield(customer_id, "deet", "sub_frequency")

        months_to_add = 0

        print("calendar_skipped: ",calendar_skipped)

        if skipped_months and (not calendar_skipped or (calendar_skipped and calendar_skipped["value"] == "false") ):
        
                months_to_add += int(float(skipped_months["value"]))

                if not calendar_skipped:
                    add_customer_metafield(customer_id, "deet", "calendar_skipped", "true", "boolean")
                else:
                    update_customer_metafield(customer_id, calendar_skipped["id"], "true")

        if sub_freq:

            val = int(float(sub_freq["value"]))

            if val != 1:
                months_to_add += val

        return_date = add_months(date, months_to_add)

        return return_date

        

    data = CalendarEvent.objects.filter(
        shopify_customer_id=customer_id,
        shopify_shop_domain=shop,
    ).order_by("event_date")

    products_per_month = get_customer_metafield(customer_id, "deet", "products_per_month")
    
    for entry in data:

        try:
            event_date = datetime.strptime(entry.event_date, '%Y-%m-%d').date()
        except:
            event_date = entry.event_date
        
        product_count = count_products_in_month_for_customer(customer_id, shop, event_date)
        #print("product_count: ",product_count)
        
        #print('products_per_month["value"]: ',products_per_month["value"])

        if products_per_month and product_count < float(products_per_month["value"]) :

            print("Adding Event: ",event_date)

            # Create a new CalendarEvent record
            calendar_event = CalendarEvent.objects.create(
                shopify_product_id=product_id,
                event_date=event_date,
                shopify_customer_id=customer_id,
                shopify_shop_domain=shop
            )
            print("calendar_event: ",calendar_event,"\n")


            return
    try:  
        last_date = data.reverse()[0].event_date
    except:
        last_date = datetime.now()

    last_date = skipped_month_sub_freq_deal(last_date, customer_id)
        
    next_date = add_months(last_date, 1)

    calendar_event = CalendarEvent.objects.create(
                shopify_product_id=product_id,
                event_date=next_date,
                shopify_customer_id=customer_id,
                shopify_shop_domain=shop
            )
    
    return


def remove_calendar_event_for_customer(customer_id, product_id, shop, date):

    try:
        event_date = datetime.strptime(date, '%Y-%m-%d').date()
    except:
        event_date = date

    print("Product TO Remove: ",product_id)
    print("Product Scehduled For: ", date)

    calendar_event = CalendarEvent.objects.filter(
            shopify_customer_id=customer_id,
            shopify_product_id=product_id,
            shopify_shop_domain=shop,
            event_date=event_date
        ).first().delete()
    
    print("Would remove: ",calendar_event)

    all_events = CalendarEvent.objects.filter(
        shopify_shop_domain=shop,
        shopify_customer_id=customer_id,
    )
    
    events_to_add = []
    for event in all_events:

        print("product: ",event.shopify_product_id)
        print("date: ",event.event_date)
        print("customer: ",event.shopify_customer_id)
        print("shop: ",event.shopify_shop_domain)
        print("needs to be added\n")

        event_data = {
            "product_id":event.shopify_product_id,
            "customer_id":event.shopify_customer_id,
            "shop":event.shopify_shop_domain,
            "date":event.event_date
        }

        events_to_add.append(event_data)
        event.delete()
    
    for event in events_to_add:
        add_calendar_event_for_customer(event["customer_id"], event["product_id"], event["shop"], event["date"])

    return {'status': 'success', 'message': 'Calendar event deleted successfully'}
   
def update_calendar_event_date_for_customer(customer_id, product_id, shop, date):

    print("product_id: ",product_id)
    print("date: ",date)
       
    if isinstance(date, str):
        try:
            event_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            # Handle invalid date string format
            raise ValueError(f"Invalid date format: {date}")
    elif isinstance(date, datetime):
        event_date = date.date()
    elif isinstance(date, dt_date):
        event_date = date
    else:
        raise TypeError(f"Unsupported date type: {type(date)}")
    
    print("setting date to: ",event_date,"\n")

    calendar_event = CalendarEvent.objects.filter(
        shopify_customer_id=customer_id,
        shopify_product_id=product_id,
        shopify_shop_domain=shop
    ).first()

    calendar_event.event_date = event_date
    calendar_event.save()

    return {'status': 'success', 'message': 'Calendar event updated successfully'}

def update_calendar_product_date_for_customer(customer_id, product_id, new_product_id ,shop, date, new_date):
    
    if isinstance(date, str):
        try:
            event_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            # Handle invalid date string format
            raise ValueError(f"Invalid date format: {date}")
    elif isinstance(date, datetime):
        event_date = date.date()
    elif isinstance(date, dt_date):
        event_date = date
    else:
        raise TypeError(f"Unsupported date type: {type(date)}")
    
    print("setting date to: ",event_date,"\n")

    
    calendar_event = CalendarEvent.objects.filter(
        shopify_customer_id=customer_id,
        shopify_product_id=product_id,
        shopify_shop_domain=shop,
        event_date=date
    ).first()

    calendar_event.event_date = new_date

    if new_product_id != product_id:
        calendar_event.shopify_product_id = new_product_id

    calendar_event.save()

    return {'status': 'success', 'message': 'Calendar event updated successfully'}

def deal_with_product_change_calendar(customer_id, shop):
    
    all_events = CalendarEvent.objects.filter(
        shopify_customer_id=customer_id,
        shopify_shop_domain=shop
    )
    
    events_to_add = []
    for event in all_events:

        print("product: ",event.shopify_product_id)
        print("date: ",event.event_date)
        print("customer: ",event.shopify_customer_id)
        print("shop: ",event.shopify_shop_domain)
        print("needs to be added\n")

        event_data = {
            "product_id":event.shopify_product_id,
            "customer_id":event.shopify_customer_id,
            "shop":event.shopify_shop_domain,
            "date":event.event_date
        }

        events_to_add.append(event_data)
        event.delete()
    
    for event in events_to_add:
        add_calendar_event_for_customer(event["customer_id"], event["product_id"], event["shop"], event["date"])

def get_all_unique_customer_calendars_for_shop(shop):

    all_events = CalendarEvent.objects.filter(
        shopify_shop_domain=shop
    ).all()

    event_details = []
    for event in all_events:

        if event.shopify_customer_id not in event_details:
            event_details.append(event.shopify_customer_id)

    return {'event_details': event_details}
