# views.py
from django.shortcuts import render
from django.db import IntegrityError, transaction
import shopify
from shopify_app.decorators import shop_login_required
from .forms import *
from .settings import *
from .models import CalendarEvent, FailedSubscriptionAttempt
from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime, timedelta, timezone

import os
import binascii

from .utils.shopify.subscriptions.create_subs import *
from .utils.shopify.subscriptions.update_subs import *
from .utils.shopify.subscriptions.get_subs import *

from .utils.shopify.customers.get_customers import *
from .utils.shopify.customers.update_customers import *

from .utils.shopify.products.update_products import * 
from .utils.shopify.products.get_products import * 

from .utils.shopify.orders.get_orders import *

from .utils.shopify.webhooks.create_webhooks import *

from .utils.shopify.cart.update_cart import *
from .utils.shopify.cart.get_cart import *

from .utils.shopify.general.product import *

from .utils.shopify.general.proxy import * 

from .utils.shopify.general.date import *

@shop_login_required
def index(request):
    products = shopify.Product.find(limit=3)
    orders = shopify.Order.find(limit=3, order="created_at DESC")
    customers = shopify.Customer.find(limit=3)

    return render(request, 'home/index.html', {'products': products, 'orders': orders, 'customers':customers})

def calendar(request):
    events = CalendarEvent.objects.all() 
    event_details = [fetch_event_details(event) for event in events]
    
    return render(request, 'calendar/calendar.html', {'event_details': event_details})

def create_event(request):
    if request.method == 'POST':
        form = CalendarEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            print("event: ", event)
            event.save()
            return redirect('calendar')
    else:
        form = CalendarEventForm()
    
    return render(request, 'calendar/create_event.html', {'form': form})

@csrf_exempt
def shopify_proxy(request):
    request_body = extract_request_body(request)

    if not request_body:
        return JsonResponse({'error': 'BODY DECODING ERROR'}, status=400)

    request_function = request_body.get('function')
    data = request_body.get('data')

    if not request_function or not data:
        return JsonResponse({'error': 'Invalid request: missing function or data'}, status=400)
    

    data_pack = json.loads(data)
    function_mapping = {
        "get_customer_data": handle_get_customer_data,
        "add_customer_product_to_calendar": handle_add_customer_product_to_calendar,
        "remove_customer_product_from_calendar": handle_remove_customer_product_from_calendar,
        "change_customer_product_date": handle_change_customer_product_date,
        "skip_number_of_months": handle_skip_number_of_months,
        "case_each_month":handle_case_each_month,
        "commited_months":handle_commited_months,
        "products_per_month":handle_products_per_month,
        "sub_frequency": handle_sub_frequency,
        "has_case_each_month":handle_has_case_each_month,
        "is_subscribed":handle_is_subscribed,
        "cancel_subscription":handle_cancel_subscription,
        "get_customer_deet_details":handle_get_customer_deet_details,
        "get_customers_next_scent":handle_get_customers_next_scent
    }

    handler = function_mapping.get(request_function)

    if handler:
        return handler(data_pack)
    else:
        return JsonResponse({'error': 'Invalid function'}, status=400)

@csrf_exempt 
def create_subscription_draft_view(request):
    if request.method == 'POST':
        form = SubscriptionDraftForm(request.POST)
        if form.is_valid():
            customer_id = form.cleaned_data['customer_id']
            billing_policy = {
                "interval": form.cleaned_data['interval'],
                "intervalCount": form.cleaned_data['interval_count'],
                "minCycles": 1
            }
            delivery_method = {
                "shipping": {
                    "address": {
                        "address1": form.cleaned_data['address1'],
                        "city": form.cleaned_data['city'],
                        "countryCode": form.cleaned_data['country_code'],
                        "firstName": form.cleaned_data['first_name'],
                        "lastName": form.cleaned_data['last_name'],
                        "provinceCode": form.cleaned_data['province_code'],
                        "zip": form.cleaned_data['zip_code']
                    },
                    "shippingOption": {
                        "code": form.cleaned_data['shipping_code'],
                        "title": form.cleaned_data['shipping_title']
                    }
                }
            }
            currency_code = form.cleaned_data['currency_code']
            next_billing_date = form.cleaned_data['next_billing_date']

            response_data = create_subscription_draft(
                customer_id,
                billing_policy,
                delivery_method,
                currency_code,
                next_billing_date,
            )

            return JsonResponse(response_data)
    else:
        form = SubscriptionDraftForm()

    return render(request, 'subscriptions/create_subscription_draft.html', {'form': form})

@csrf_exempt
def add_line_item_view(request):
    if request.method == 'POST':
        form = AddLineItemForm(request.POST)
        if form.is_valid():
            draft_id = form.cleaned_data['draft_id']
            variant_id = form.cleaned_data['variant_id']
            quantity = form.cleaned_data['quantity']

            response_data = add_line_item_to_draft(draft_id, variant_id, quantity)

            return JsonResponse(response_data)
    else:
        form = AddLineItemForm()

    return render(request, 'subscriptions/add_line_item.html', {'form': form})


def view_draft_view(request):
    if request.method == 'POST':
        form = ViewDraftForm(request.POST)
        if form.is_valid():
            draft_id = form.cleaned_data['draft_id']

            response_data = get_subscription_draft(draft_id)

            return JsonResponse(response_data)
    else:
        form = ViewDraftForm()

    return render(request, 'subscriptions/view_draft.html', {'form': form})

@csrf_exempt
def commit_draft_view(request):
    if request.method == 'POST':
        form = CommitDraftForm(request.POST)
        if form.is_valid():
            draft_id = form.cleaned_data['draft_id']

            response_data = commit_subscription_draft(draft_id)

            return JsonResponse(response_data)
    else:
        form = CommitDraftForm()

    return render(request, 'subscriptions/commit_draft.html', {'form': form})

@csrf_exempt
def add_subscription_plan_view(request):
    if request.method == 'POST':
        form = AddSubscriptionPlanForm(request.POST)
        if form.is_valid():
            # input = {
            #     "name": form.cleaned_data['name'],
            #     "merchantCode": form.cleaned_data['merchant_code'],
            #     "options": [form.cleaned_data['option']],
            #     "sellingPlansToCreate": [
            #         {
            #             "name": form.cleaned_data['plan_name'],
            #             "options": form.cleaned_data['plan_option'],
            #             "category": "SUBSCRIPTION",
            #             "billingPolicy": {
            #                 "recurring": {
            #                     "interval": form.cleaned_data['interval'],
            #                     "intervalCount": form.cleaned_data['interval_count'],
            #                 }
            #             },
            #             "pricingPolicies": [
            #                 {
            #                     "fixed": {
            #                         "adjustmentType": "PERCENTAGE",
            #                         "adjustmentValue": {
            #                             "percentage": float(form.cleaned_data['percentage'])
            #                         }
            #                     }
            #                 }
            #             ],
            #             "deliveryPolicy": {
            #                 "recurring": {
            #                     "interval": form.cleaned_data['delivery_interval'],
            #                     "intervalCount": form.cleaned_data['delivery_interval_count'],
            #                 }
            #             }
            #         }
            #     ]
            # }

            resources = {
                "productVariantIds": [format_product_id(form.cleaned_data['product_id'])],
            }

            response_data = create_subscription_sc_selling_group(resources)

            return JsonResponse(response_data)
    else:
        form = AddSubscriptionPlanForm()
        return render(request, 'subscriptions/add_subscription_plan.html', {'form': form})

def view_subscription_plan_view(request):
    if request.method == 'POST':
        form = ViewSubscriptionPlanForm(request.POST)
        if form.is_valid():
            plan_id = form.cleaned_data['plan_id']
            response_data = get_subscription_plan(plan_id)

            return JsonResponse(response_data)
    else:
        form = ViewSubscriptionPlanForm()

    return render(request, 'subscriptions/view_subscription_plan.html', {'form': form})

def view_all_subscription_contracts(request):
    response_data = get_all_subscription_contracts()
    return render(request, 'subscriptions/view_all_subscription_contracts.html', {'response_data': response_data})

# View to change product variant in a subscription contract
def subscription_contract_product_change_view(request):
    if request.method == 'POST':
        form = SubscriptionContractProductChangeForm(request.POST)
        if form.is_valid():
            contract_id = form.cleaned_data['contract_id']
            line_id = form.cleaned_data['line_id']
            variant_id = form.cleaned_data['variant_id']
            price = float(form.cleaned_data['price'])
            
            response_data = subscription_contract_product_change(contract_id, line_id, variant_id, price)
            
            return JsonResponse(response_data)
    else:
        form = SubscriptionContractProductChangeForm()

    return render(request, 'subscriptions/subscription_contract_product_change.html', {'form': form})

# View to create a subscription billing attempt
@csrf_exempt
def create_subscription_billing_attempt_view(request):

    if request.method == 'POST':
        form = CreateSubscriptionBillingAttemptForm(request.POST)
        if form.is_valid():

            contract_id = form.cleaned_data['contract_id']
            index = form.cleaned_data['index']
            origin_time = form.cleaned_data['origin_time']

            print("origin_time: ",origin_time)
            
            response_data = create_subscription_billing_attempt(contract_id, index, origin_time=origin_time)
            
            return JsonResponse(response_data)
    else:
        form = CreateSubscriptionBillingAttemptForm()

    return render(request, 'subscriptions/create_subscription_billing_attempt.html', {'form': form})

# View to get the details of a subscription billing attempt
@csrf_exempt
def view_subscription_billing_attempt_view(request):
    response_data = None
    if request.method == 'POST':
        form = ViewSubscriptionBillingAttemptForm(request.POST)
        if form.is_valid():
            billing_attempt_id = form.cleaned_data['billing_attempt_id']
            
            response_data = get_subscription_billing_attempt(billing_attempt_id)
            return JsonResponse(response_data)
    else:
        form = ViewSubscriptionBillingAttemptForm()

    return render(request, 'subscriptions/view_subscription_billing_attempt.html', {'form': form, 'response_data': response_data})

def dealWithCalendar(customer_id):

    events = CalendarEvent.objects.filter(shopify_customer_id=customer_id)
    event_details = [fetch_event_details(event) for event in events]

    print(event_details)

@csrf_exempt
def order_payment_view(request):

    billing_policy = None

    print("header: ",request.headers)

    body_data = json.loads(request.body)
    print("Body: ", json.dumps(body_data, indent=4),"\n\n")

    print("Headers: ")
    for header, value in request.headers.items():
        print(f"{header}: {value}")

    # Print request body
    if request.body:
        try:
            body_data = json.loads(request.body)
            order_data = get_order_details(body_data)

            session = shopify.Session("247c21-78.myshopify.com", "unstable", "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")
            shopify.ShopifyResource.activate_session(session)

            dealWithCalendar(order_data["customer_id"])
            customer_details = is_customer_subscribed(order_data["customer_id"])

            if customer_details != False:
                products_per_month = get_customer_metafield(order_data["customer_id"], "deet", "products_per_month")
                update_subscription_product_based_on_calendar_record(order_data["customer_id"], products_per_month["value"])
            else:
                details = get_new_sub_data_from_order(body_data["id"])
                #print("details: ", details)

                billing_policy = {
                    "interval": "MONTH",
                    "intervalCount": 1,
                    "minCycles": 1
                }

                delivery_method = {
                    "shipping": {
                        "address": {
                            "address1": details['address1'],
                            "address2": details['address2'],
                            "city": details['city'],
                            "countryCode": details['countryCodeV2'],
                            "firstName": details['firstName'],
                            "lastName": details['lastName'],
                            "provinceCode": details['provinceCode'],
                            "zip": details['zip']
                        },
                        "shippingOption": {
                            "code": "sub",
                            "title": "sub-shipping"
                        }
                    }
                }

                #print("billing_policy: ", billing_policy)

                draft_id = get_subscription_draft_id(
                    create_subscription_draft(
                        order_data["customer_id"],
                        billing_policy,
                        delivery_method,
                        "GBP",
                        next_month_10th()
                    ), src="subscriptionContractCreate"
                )

                print("draft_id: ", draft_id,"\n")

                print("details['variant_ids']: ",details['variant_ids'],"\n")

                for variant_id in details['variant_ids']:
                    add_line_item_to_draft(draft_id, variant_id, 1)

                commit_subscription_draft(draft_id)

                print("BANG ALL CREATED go AND CHECK")

            return JsonResponse({"status": "success"})

        except json.JSONDecodeError:
            print("Request Body:", request.body.decode('utf-8'))
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    else:
        print("BODY ISSUE")
        return JsonResponse({"error": "No body in request"}, status=400)


def view_customer(request):
    if request.method == 'POST':
        form = CustomerIDForm(request.POST)
        if form.is_valid():
            customer_id = form.cleaned_data['customer_id']
            customer_details = get_customer_details(customer_id)
            return JsonResponse(customer_details)#render(request, 'customers/customer_details.html', {'customer_details': customer_details})
    else:
        form = CustomerIDForm()
    return render(request, 'customers/customer_form.html', {'form': form})

def view_customer_subscription(request):
    if request.method == 'POST':
        form = CustomerIDForm(request.POST)
        if form.is_valid():
            customer_id = form.cleaned_data['customer_id']
            customer_details = is_customer_subscribed(customer_id)
            return JsonResponse(customer_details)#render(request, 'customers/customer_subscription_contracts.html', {'customer_details': customer_details})
    else:
        form = CustomerIDForm()
    return render(request, 'customers/customer_form.html', {'form': form})

def set_next_billing_date_view(request):
    if request.method == 'POST':
        form = NextBillingDateForm(request.POST)
        if form.is_valid():
            contract_id = form.cleaned_data['contract_id']
            next_billing_date = form.cleaned_data['next_billing_date']
            next_billing_date = next_billing_date.isoformat(timespec='seconds')
            response_data = set_next_billing_date(contract_id, next_billing_date)
            return JsonResponse(response_data)
    else:
        form = NextBillingDateForm()

    return render(request, 'subscriptions/set_next_billing_date.html', {'form': form})

@csrf_exempt
def view_subscription_billing_cycles(request):

    response_data = None
    print("request.method: ",request.method)
    if request.method == 'POST':
        form = SubscriptionBillingCycleForm(request.POST)
        if form.is_valid():
            contract_id = form.cleaned_data['contract_id']
            response_data = get_billing_cycles(contract_id)
            
    else:
        form = SubscriptionBillingCycleForm()

    return render(request, 'subscriptions/view_subscription_billing_cycle.html', {'form': form, 'response_data': response_data})

def add_metafield_view(request):
    if request.method == 'POST':
        form = ProductMetafieldForm(request.POST)
        if form.is_valid():
            product_id = form.cleaned_data['product_id']
            namespace = form.cleaned_data['namespace']
            key = form.cleaned_data['key']
            value = form.cleaned_data['value']
            value_type = form.cleaned_data['value_type']

            result = add_product_metafield(product_id, namespace, key, value, value_type)
            return JsonResponse(result)
    else:
        form = ProductMetafieldForm()

    return render(request, 'products/add_metafield.html', {'form': form})

def view_product_details(request):
    if request.method == 'POST':
        form = ProductIDForm(request.POST)
        if form.is_valid():
            product_id = form.cleaned_data['product_id']

            result = get_product_details(product_id)
            return JsonResponse(result)
    else:
        form = ProductIDForm()

    return render(request, 'products/view_product.html', {'form': form})

def update_metafield_view(request):
    if request.method == 'POST':
        form = UpdateProductMetafieldForm(request.POST)
        if form.is_valid():
            product_id = form.cleaned_data['product_id']
            metafield_id = form.cleaned_data['metafield_id']
            value = form.cleaned_data['value']

            result = update_product_metafield(product_id, metafield_id, value)
            return JsonResponse(result)
    else:
        form = UpdateProductMetafieldForm()

    return render(request, 'products/update_metafield.html', {'form': form})

def get_metafield_view(request):
    if request.method == 'POST':
        form = UpdateProductMetafieldForm(request.POST)
        if form.is_valid():
            product_id = form.cleaned_data['product_id']
            metafield_id = form.cleaned_data['metafield_id']
            value = form.cleaned_data['value']

            result = update_product_metafield(product_id, metafield_id, value)
            return JsonResponse(result)
    else:
        form = UpdateProductMetafieldForm()

    return render(request, 'products/update_metafield.html', {'form': form})

def view_subscription_lines(request):

    response_data = None
    print("request.method: ",request.method)
    if request.method == 'POST':
        form = ViewSubscriptionContractForm(request.POST)
        if form.is_valid():
            contract_id = form.cleaned_data['contract_id']
            response_data = get_subscription_line_item(contract_id)
            return JsonResponse(response_data)
            
    else:
        form = ViewSubscriptionContractForm()

    return render(request, 'subscriptions/view_sub_lines.html', {'form': form})

def view_product_variant(request):
    if request.method == 'POST':
        form = ProductIDForm(request.POST)
        if form.is_valid():
            product_id = form.cleaned_data['product_id']

            result = get_product_variant_details(product_id)
            return JsonResponse(result)
    else:
        form = ProductIDForm()

    return render(request, 'products/view_variant.html', {'form': form})

def clear_customer_calendar(request):
    if request.method == 'POST':
        form = CustomerIDForm(request.POST)
        if form.is_valid():
            customer_id = form.cleaned_data['customer_id']
            deleted_count, _ = CalendarEvent.objects.filter(shopify_customer_id=customer_id).delete()
            return JsonResponse({"CLEARED":deleted_count})
    else:
        form = CustomerIDForm()

    return render(request, 'customers/clear_calendar.html', {'form': form})

def get_sub_customer_view(request):
    
    response_data = None
    print("request.method: ",request.method)
    if request.method == 'POST':
        form = ViewSubscriptionContractForm(request.POST)
        if form.is_valid():
            contract_id = form.cleaned_data['contract_id']
            response_data = get_sub_contract_customer(contract_id)
            return JsonResponse({"DONE":response_data})
            
    else:
        form = ViewSubscriptionContractForm()

    return render(request, 'subscriptions/view_sub_lines.html', {'form': form})

def update_sub_product_via_calendar_view(request):
    
    response_data = None
    print("request.method: ",request.method)
    if request.method == 'POST':
        form = ViewSubscriptionContractForm(request.POST)
        if form.is_valid():
            
            contract_id = form.cleaned_data['contract_id']
            customer_id = get_sub_contract_customer(contract_id)
            customer_id = customer_id.split('/')[-1]

            calendar_event = CalendarEvent.objects.filter(
                shopify_customer_id=customer_id
            ).order_by('event_date').first()
            
            print("CALENDAR EVENT: ",calendar_event)

            response_data = update_subscription_product_based_on_calendar_record(contract_id, calendar_event)
            return JsonResponse(response_data)
            
    else:
        form = ViewSubscriptionContractForm()

    return render(request, 'subscriptions/view_sub_lines.html', {'form': form})

def expire_subscription_contract_view(request):
    if request.method == 'POST':
        form = SubscriptionContractExpireForm(request.POST)
        if form.is_valid():
            subscription_contract_id = form.cleaned_data['subscription_contract_id']
            
            result = expire_subscription_contract(subscription_contract_id)
            return JsonResponse(result)
    else:
        form = SubscriptionContractExpireForm()

    return render(request, 'subscriptions/expire_subscription_contract.html', {'form': form})

def add_variants_to_selling_plan_group_view(request):

    if request.method == 'POST':
        form = SellingPlanGroupAddVariantsForm(request.POST)
        if form.is_valid():
            selling_plan_group_id = form.cleaned_data['selling_plan_group_id']
            product_variant_ids = form.cleaned_data['product_variant_ids'].split(',')

            result = add_variants_to_selling_plan_group(selling_plan_group_id, product_variant_ids)
            return JsonResponse(result)
    else:
        form = SellingPlanGroupAddVariantsForm()

    return render(request, 'subscriptions/add_variants_to_selling_plan_group.html', {'form': form})

def add_metafield_cusomter_view(request):
    if request.method == 'POST':
        form = CustomerMetafieldForm(request.POST)
        if form.is_valid():
            customer_id = form.cleaned_data['customer_id']
            namespace = form.cleaned_data['namespace']
            key = form.cleaned_data['key']
            value = form.cleaned_data['value']
            value_type = form.cleaned_data['value_type']

            result = add_customer_metafield(customer_id, namespace, key, value, value_type)
            return JsonResponse(result)
    else:
        form = CustomerMetafieldForm()

    return render(request, 'customers/add_metafield.html', {'form': form})

def update_customer_metafield_view(request):
    if request.method == 'POST':
        form = UpdateCustomerMetafieldForm(request.POST)
        if form.is_valid():
            customer_id = form.cleaned_data['customer_id']
            metafield_id = form.cleaned_data['metafield_id']
            value = form.cleaned_data['value']

            result = update_customer_metafield(customer_id, metafield_id, value)
            return JsonResponse(result)
    else:
        form = UpdateCustomerMetafieldForm()

    return render(request, 'customers/update_metafield.html', {'form': form})

def get_customer_metafield_view(request):
    if request.method == 'POST':
        form = CustomerIDForm(request.POST)
        if form.is_valid():
            customer_id = form.cleaned_data['customer_id']

            result = get_customer_metafield_data(customer_id)
            return JsonResponse(result)
    else:
        form = CustomerIDForm()

    return render(request, 'customers/get_metafields.html', {'form': form})

def get_customer_specific_metafield_view(request):
    if request.method == 'POST':
        form = CustomerSpecificMetafieldForm(request.POST)
        if form.is_valid():
            customer_id = form.cleaned_data['customer_id']
            namespace = form.cleaned_data['namespace']
            key = form.cleaned_data['key']

            result = get_customer_metafield(customer_id, namespace, key)
            return JsonResponse(result)
    else:
        form = CustomerSpecificMetafieldForm()

    return render(request, 'customers/get_specific_metafield.html', {'form': form})

@csrf_exempt
def create_webhook_view(request):

    session = shopify.Session("247c21-78.myshopify.com", "unstable", "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") #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
    shopify.ShopifyResource.activate_session(session)

    if request.method == 'POST':
        form = WebhookSubscriptionForm(request.POST)
        if form.is_valid():
            topic = form.cleaned_data['topic']
            callback_url = form.cleaned_data['callback_url']
            format = form.cleaned_data['format']
            
            response_data = create_webhook_subscription(topic, callback_url, format)
            return JsonResponse(response_data)
    else:
        form = WebhookSubscriptionForm()

    return render(request, 'webhooks/create_webhook.html', {'form': form})

@csrf_exempt
def cart_check_view(request):
    request_info = {
        'method': request.method,
        'path': request.path,
        'GET': request.GET.dict(),
        'POST': request.POST.dict(),
        'body': request.body.decode('utf-8') if request.body else None,
        'headers': {k: v for k, v in request.headers.items()}
    }

    #print("REQUEST: ", json.dumps(request_info, indent=2), "\n\n\n")

    if request_info['body']:
        
        try:
            
            session = shopify.Session("247c21-78.myshopify.com", "unstable", "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")
            shopify.ShopifyResource.activate_session(session)

            data = json.loads(request_info['body'])
            print("BODY: ", json.dumps(data, indent=2),"\n\n\n\n")

            cart_id = data["id"]
    
            if 'line_items' in data:
        
                remove_fees(cart_id, data['line_items'])
                add_cart_fees(cart_id, data['line_items'])
               

        except json.JSONDecodeError:
            print("BODY: Invalid JSON format")

    return JsonResponse({"good": "stuff"})

@csrf_exempt
def test(request):
    print("Request Method:", request.method, "\n\n")
    print("Request GET Parameters:", request.GET, "\n\n")
    print("Request POST Parameters:", request.POST, "\n\n")
    print("Request Headers:", request.headers, "\n\n")
    print("Request Body:", request.body, "\n\n")
    print("Request User:", request.user, "\n\n")

    session = shopify.Session("247c21-78.myshopify.com", "unstable", "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") 
    shopify.ShopifyResource.activate_session(session)

    customers = shopify.Customer.find(limit=10)
    
    response = render(request, 'embed/home.html', {'customers': customers})
    response['Content-Security-Policy'] = "default-src 'self' *; style-src 'self' * 'unsafe-inline' https://valid-strongly-raptor.ngrok-free.app; script-src 'self' * 'unsafe-inline' 'unsafe-eval'; frame-ancestors *;"
    return response

@csrf_exempt
def embed_customer(request, customer_id):

    session = shopify.Session("247c21-78.myshopify.com", "unstable", "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") #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
    shopify.ShopifyResource.activate_session(session)

    customer = get_customer_details(customer_id)
    calendar = get_calendar_events_for_customer(customer_id, "247c21-78.myshopify.com")
    subscription = get_first_active_sub(get_customer_subscription_contracts(customer_id))
    past_orders = get_customer_orders(customer_id)

    print("calendar: ",calendar)

    if subscription:
        subscription['nextBillingDate'] = datetime.strptime(subscription['nextBillingDate'], "%Y-%m-%dT%H:%M:%SZ")
        subscription["id"] = subscription["id"].replace("gid://shopify/SubscriptionContract/", "")

    for order in past_orders['data']['orders']['edges']:
        order['node']['createdAt'] = datetime.strptime(order['node']['createdAt'], "%Y-%m-%dT%H:%M:%SZ")

    # Sort orders by createdAt descending
    past_orders['data']['orders']['edges'].sort(key=lambda x: x['node']['createdAt'], reverse=True)
  
    return render(request, 'embed/customer.html', {'customer': customer, 'customer_id':customer_id, 'calendar':calendar, 'subscription':subscription, 'past_orders':past_orders})

@csrf_exempt
def embed_subscription(request, subsrciption_id):

    def filter_billing_cycles(billing_cycles):
        now = datetime.now()  
        three_months_ago = now - timedelta(days=90)
        six_months_from_now = now + timedelta(days=180)

        filtered_cycles = []
        for cycle in billing_cycles:

            billing_date_str = cycle['node']['billingAttemptExpectedDate']
            billing_date = datetime.strptime(billing_date_str, "%Y-%m-%dT%H:%M:%SZ")

            if three_months_ago <= billing_date <= six_months_from_now:
                cycle['node']['billingAttemptExpectedDate'] = billing_date
                filtered_cycles.append(cycle)
        
        return filtered_cycles

    session = shopify.Session("247c21-78.myshopify.com", "unstable", "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") #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
    shopify.ShopifyResource.activate_session(session)

    #billing_attempts = unwrap_subscription_billing_attempt(get_subscription_billing_attempt(subsrciption_id))
   
    products = get_subscription_line_item(subsrciption_id)

    customer = get_sub_contract_customer(subsrciption_id)
    customer = get_customer_details(customer)

    if customer:
        customer["id"] = customer["id"].replace("gid://shopify/Customer/", "")

    subscription = get_basic_sub_info(subsrciption_id)
    past_orders = get_customer_orders(customer["id"])

    #print("past orders: ",past_orders)

    if subscription:
        subscription['nextBillingDate'] = datetime.strptime(subscription['nextBillingDate'], "%Y-%m-%dT%H:%M:%SZ")
        subscription['updatedAt'] = datetime.strptime(subscription['updatedAt'], "%Y-%m-%dT%H:%M:%SZ")
        subscription["id"] = subscription["id"].replace("gid://shopify/SubscriptionContract/", "")

    billing_cycles = get_billing_cycles(subsrciption_id)
    filtered_billing_cycles = filter_billing_cycles(billing_cycles)

    for order in past_orders['data']['orders']['edges']:
        order['node']['createdAt'] = datetime.strptime(order['node']['createdAt'], "%Y-%m-%dT%H:%M:%SZ")

    # Sort orders by createdAt descending
    past_orders['data']['orders']['edges'].sort(key=lambda x: x['node']['createdAt'], reverse=True)

    return render(request, 'embed/subscription.html', {"products":products,  
                                                       "customer":customer, 
                                                       "subscription":subscription,
                                                       "billing_cycles":filtered_billing_cycles,
                                                       "past_orders":past_orders})

@csrf_exempt
def embed_cancel_sub(request, subsrciption_id):

    session = shopify.Session("247c21-78.myshopify.com", "unstable", "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") #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
    shopify.ShopifyResource.activate_session(session)
    
    cancel_subscription(subsrciption_id)

    return redirect("embed_subscription", subsrciption_id=subsrciption_id)

@csrf_exempt
def embed_skip_sub_month(request, subsrciption_id, customer_id):

    session = shopify.Session("247c21-78.myshopify.com", "unstable", "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") #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
    shopify.ShopifyResource.activate_session(session)
    
    customer_skip_months(customer_id, "247c21-78.myshopify.com", 1)

    return redirect("embed_subscription", subsrciption_id=subsrciption_id)

@csrf_exempt
def embed_renew_subscription(request, subsrciption_id):

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
        #print("Next billing_cycles: ",)

    return redirect("embed_subscription", subsrciption_id=subsrciption_id)

@csrf_exempt
def embed_update_customer_deets(request, customer_id):

    shop = "247c21-78.myshopify.com"

    session = shopify.Session(shop, "unstable", "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") #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
    shopify.ShopifyResource.activate_session(session)

    if request.method == 'POST':

        products_per_month = float(request.POST.get('products_per_month', 1.0))
        sub_frequency = float(request.POST.get('sub_frequency', 1.0))
        skipped_months = float(request.POST.get('skipped_months', 0.0))
        commited_months = float(request.POST.get('commited_months', 1.0))
        case_each_month = bool(request.POST.get('case_each_month', False))


        customer_skip_months(customer_id, shop, skipped_months)
        customer_commited_months(customer_id, commited_months)

        customer_products_per_month(customer_id, products_per_month)
        deal_with_product_change_calendar(customer_id, shop)
        
        customer_sub_frequency(customer_id, sub_frequency)
        

    return redirect('embed_customer', customer_id=customer_id)

@csrf_exempt
def embed_remove_customer_product_calendar(request, customer_id, product_id, event_date):

    shop = "247c21-78.myshopify.com"

    session = shopify.Session(shop, "unstable", "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")
    shopify.ShopifyResource.activate_session(session)

    remove_calendar_event_for_customer(customer_id, product_id, shop, event_date)

    return redirect('embed_customer', customer_id=customer_id)

@csrf_exempt
def embed_update_customer_product_calendar(request, customer_id, product_id, event_date):
    if request.method == 'GET':
        # Render a form for the user to confirm the removal
        form = UpdateEventForm(initial={'date': event_date, 'product_id': product_id})
        context = {
            'form': form,
            'customer_id': customer_id
        }
        return render(request, 'embed/update_calendar.html', context)
    
    elif request.method == 'POST':

        form = UpdateEventForm(request.POST)
        
        if form.is_valid():

            new_date = form.cleaned_data['date']
            new_product_id = form.cleaned_data['product_id']

            # Perform the removal action
            shop = "247c21-78.myshopify.com"
            session = shopify.Session(shop, "unstable", "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")
            shopify.ShopifyResource.activate_session(session)

            update_calendar_event_date_for_customer(customer_id, product_id, shop, event_date)

            return redirect('embed_customer', customer_id=customer_id)
        
@csrf_exempt
def embed_add_customer_product_calendar(request, customer_id):
    if request.method == 'GET':
        # Render a form for the user to confirm the removal
        form = UpdateEventForm()
        context = {
            'form': form,
            'customer_id': customer_id,
            'add':True
        }
        return render(request, 'embed/update_calendar.html', context)
    
    elif request.method == 'POST':

        form = UpdateEventForm(request.POST)
        
        if form.is_valid():

            new_date = form.cleaned_data['date']
            new_product_id = form.cleaned_data['product_id']

            # Perform the removal action
            shop = "247c21-78.myshopify.com"
            session = shopify.Session(shop, "unstable", "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")
            shopify.ShopifyResource.activate_session(session)

            add_calendar_event_for_customer(customer_id, new_product_id, shop, new_date)

            return redirect('embed_customer', customer_id=customer_id)
        
@csrf_exempt
def embed_update_customer_contact_info(request, customer_id):

    shop = "247c21-78.myshopify.com"

    session = shopify.Session(shop, "unstable", "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") #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
    shopify.ShopifyResource.activate_session(session)

    if request.method == 'POST':
        
        first_name = str(request.POST.get('first_name', ''))
        last_name = str(request.POST.get('last_name', ''))
        email = str(request.POST.get('email', ''))
        phone = str(request.POST.get('phone', ''))

        update_customer_contact_details(customer_id, first_name, last_name, email, phone)
        

    return redirect('embed_customer', customer_id=customer_id)

@csrf_exempt
def embed_calendars(request):

    shop = "247c21-78.myshopify.com"
    session = shopify.Session(shop, "unstable", "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") #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
    shopify.ShopifyResource.activate_session(session)

    calendars = get_all_unique_customer_calendars_for_shop(shop)
    print(calendars)

    return render(request, 'embed/calendars.html', {'calendars': calendars})

@csrf_exempt
def embed_customer_calendars(request, customer_id):

    shop = "247c21-78.myshopify.com"
    session = shopify.Session(shop, "unstable", "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") #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
    shopify.ShopifyResource.activate_session(session)

    calendar = get_calendar_events_for_customer(customer_id, "247c21-78.myshopify.com")
    print("calendar - customers: ",calendar)

    return render(request, 'embed/customer_calendar.html', {"customer_id":customer_id, "calendar":calendar})

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt 
def embed_subscriptions(request):
    
    def unwrap_subscription_data(subs):
        # Extract the subscription contracts
        contracts = subs['data']['subscriptionContracts']['edges']

        status_count = {
            "ACTIVE":0,
            "CANCELLED":0,
            "PAUSED":0,
            "ALL":0
        }

        # Unwrap the details
        unwrapped_contracts = []
    
        for contract in contracts:
            node = contract['node']
            unwrapped_contract = {
                'id': node['id'].replace("gid://shopify/SubscriptionContract/", ""),
                'status': node['status'],
                'customer': {
                    'firstName': node['customer']['firstName'],
                    'lastName': node['customer']['lastName']
                }
            }
            unwrapped_contracts.append(unwrapped_contract)
            status_count[node['status']] += 1
            status_count["ALL"] += 1
            
        return unwrapped_contracts, status_count

    # Shopify session setup
    shop = "247c21-78.myshopify.com"
    session = shopify.Session(shop, "unstable", "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")
    shopify.ShopifyResource.activate_session(session)

    # Check for the 'id' parameter in the GET request
    subscription_id = request.GET.get('id', None)
    if subscription_id:
        return redirect("embed_subscription", subsrciption_id=subscription_id)

    # Fetch all subscription contracts
    subs, status_count = unwrap_subscription_data(get_all_subscription_contracts())

    # Get the status filter from the request (POST method)
    if request.method == 'POST':
        status_filter = request.POST.get('status', 'all').lower()
        print("POSTED")
    else:
        status_filter = 'all'

    # Filter the subscriptions based on the status
    if status_filter != 'all':
        subs = [sub for sub in subs if sub['status'].lower() == status_filter]

    return render(request, 'embed/subscriptions.html', {'subscriptions': subs, "status_count":status_count})



@csrf_exempt
def embed_change_subscription_product(request, subsrciption_id, lineID):

    if request.method == 'POST':

        productForm = ProductChangeForm(request.POST)

        if productForm.is_valid():

            shop = "247c21-78.myshopify.com"
            session = shopify.Session(shop, "unstable", "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") #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
            shopify.ShopifyResource.activate_session(session)

            print("SKU: ",productForm.cleaned_data["product_sku"])

            id = get_product_variant_id_via_sku(productForm.cleaned_data["product_sku"])
            premium_value = get_variants_premium_value(id)
            print("ID: ",id," premium_value: ",premium_value)
            subscription_contract_product_change(subsrciption_id, lineID, id, (14+premium_value))

            return redirect("embed_subscription", subsrciption_id=subsrciption_id)
    else:
        productForm = ProductChangeForm()

    return render(request, 'embed/change_sub_product.html', {'form': productForm, "subsrciption_id":subsrciption_id, "lineID":lineID})

@csrf_exempt
def embed_add_subscription_product(request, subsrciption_id):

    if request.method == 'POST':

        productForm = ProductChangeForm(request.POST)

        if productForm.is_valid():

            shop = "247c21-78.myshopify.com"
            session = shopify.Session(shop, "unstable", "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") #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
            shopify.ShopifyResource.activate_session(session)

            print("SKU: ",productForm.cleaned_data["product_sku"])

            id = get_product_variant_id_via_sku(productForm.cleaned_data["product_sku"])
            premium_value = get_variants_premium_value(id)

            draft_id = format_subscriptionDraft_id(put_sub_into_update_draft(subsrciption_id))
            add_line_item_to_draft(draft_id, id, 1, premium_value)
            commit_subscription_draft(draft_id)

            return redirect("embed_subscription", subsrciption_id=subsrciption_id)
    else:
        productForm = ProductChangeForm()

    return render(request, 'embed/add_sub_product.html', {'form': productForm, 'subsrciption_id':subsrciption_id})

@csrf_exempt
def embed_remove_subscription_product(request, subsrciption_id, lineID):

    shop = "247c21-78.myshopify.com"
    session = shopify.Session(shop, "unstable", "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") #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
    shopify.ShopifyResource.activate_session(session)

    draft_id = format_subscriptionDraft_id(put_sub_into_update_draft(subsrciption_id))
    subscription_contract_product_remove(draft_id, lineID)
    commit_subscription_draft(draft_id)

    return redirect("embed_subscription", subsrciption_id=subsrciption_id)

@csrf_exempt
def customer_payment_view(request, customer_id):
    return JsonResponse(get_payment_ids_for_customer(customer_id))

@csrf_exempt
def view_webhooks(request):

    shop = "247c21-78.myshopify.com"
    session = shopify.Session(shop, "unstable", "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") #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
    shopify.ShopifyResource.activate_session(session)

    query = """
        query {
        webhookSubscriptions(first: 100) {
            edges {
            node {
                topic
                endpoint {
                __typename
                ... on WebhookHttpEndpoint {
                    callbackUrl
                }
                ... on WebhookEventBridgeEndpoint {
                    arn
                }
                ... on WebhookPubSubEndpoint {
                    pubSubProject
                    pubSubTopic
                }
                }
            }
            }
        }
        }
    """

    response = shopify.GraphQL().execute(query)
    response_data = json.loads(response)

    return JsonResponse(get_payment_ids_for_customer(response_data))

@csrf_exempt
def get_details(request):
    # Extract and format headers
    headers = {header: value for header, value in request.headers.items()}
    formatted_headers = json.dumps(headers, indent=4)

    # Extract and format body
    try:
        if request.body:
            body_data = json.loads(request.body)
            formatted_body = json.dumps(body_data, indent=4)
        else:
            formatted_body = "No body in request"
    except json.JSONDecodeError:
        formatted_body = request.body.decode('utf-8')

    print("body_data: ",formatted_body)
    print("formatted_headers: ",formatted_headers)

    # Combine headers and body into a single formatted string
    details = {
        "headers": formatted_headers,
        "body": formatted_body
    }

    # Return as JSON response
    return JsonResponse(details)


def create_plan_view(request):

    return JsonResponse(create_subscription_sc_selling_group())

@csrf_exempt
def add_product_to_selling_group_view(request):
    if request.method == 'POST':
        form = SellingGroupAddForm(request.POST)
        if form.is_valid():

            shop = "247c21-78.myshopify.com"
            session = shopify.Session(shop, "unstable", "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") #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
            shopify.ShopifyResource.activate_session(session)

            # Process the form data here
            selling_group_id = form.cleaned_data['selling_group_id']
            product_variant_id = form.cleaned_data['product_variant_id']
            # Add the logic to handle adding the product to the selling group
            return JsonResponse(add_product_to_selling_plan_group(selling_group_id, [product_variant_id]))
    else:
        form = SellingGroupAddForm()

    return render(request, 'subscriptions/add_product_selling_group.html', {'form': form})

@csrf_exempt
def delete_webhook(request, webhook_id):

    shop = "247c21-78.myshopify.com"
    session = shopify.Session(shop, "unstable", "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") #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
    shopify.ShopifyResource.activate_session(session)

    query = """
        mutation webhookSubscriptionDelete($id: ID!) {
        webhookSubscriptionDelete(id: $id) {
            userErrors {
            field
            message
            }
            deletedWebhookSubscriptionId
        }
        }
    """

    variables = {
        "id":f"gid://shopify/WebhookSubscription/{webhook_id}"
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    response_data = json.loads(response)

    return JsonResponse(response_data)

@csrf_exempt
def deal_with_subscription_creation(request):

    headers = {header: value for header, value in request.headers.items()}
    formatted_headers = json.dumps(headers, indent=4)

    # Extract and format body
    try:
        if request.body:
            body_data = json.loads(request.body)
            formatted_body = json.dumps(body_data, indent=4)
        else:
            formatted_body = "No body in request"
    except json.JSONDecodeError:
        formatted_body = request.body.decode('utf-8')
    
    print("formatted_body: ",formatted_body,"\n\n")

    shop = "247c21-78.myshopify.com"
    session = shopify.Session(shop, "unstable", "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") #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
    shopify.ShopifyResource.activate_session(session)

    # Get the 10th of the next month
    today = datetime.today()
    if today.month == 12:  # December
        next_month = 1
        year = today.year + 1
    else:
        next_month = today.month + 1
        year = today.year

    next_billing_date = datetime(year, next_month, 10)

    # Assuming `body_data` is a dictionary and `id` is a key in this dictionary
    subscription_id = body_data.get('id')
    order_id = body_data.get('origin_order_id')
    customer_id = get_sub_contract_customer(subscription_id)

    customer_sub_frequency(customer_id, 1)
    customer_products_per_month(customer_id, 1)
    customer_commited_months(customer_id, 0)
    customer_case_each_month(customer_id, value="false")
    customer_skip_months(customer_id, shop, 0)

    calendar_skipped = get_customer_metafield(customer_id, "deet", "calendar_skipped")
    if not calendar_skipped:
        add_customer_metafield(customer_id, "deet", "calendar_skipped", "false", "boolean")
    else:
        update_customer_metafield(customer_id, calendar_skipped["id"], "false")

    # Call the function to set the next billing date
    set_next_billing_date(subscription_id, next_billing_date)
    add_tag_to_order(order_id, tag_text="parent")
    add_product_to_order(order_id, 0, "CASE", "CASE")
    add_product_to_order(order_id, 0, "LEAFLET", "LEAFLET")
    products = get_sub_line_variant_ids(subscription_id)

    for product in products:
        premium_value = get_variants_premium_value(product["variant_id"])
        price = 14 + premium_value
        subscription_contract_product_change(subscription_id, product["line_id"], product["variant_id"], price)

    return JsonResponse({"status": "success"})


@csrf_exempt
def deal_with_subscription_renewal(request):

    headers = {header: value for header, value in request.headers.items()}
    formatted_headers = json.dumps(headers, indent=4)

    # Extract and format body
    try:
        if request.body:
            body_data = json.loads(request.body)
            formatted_body = json.dumps(body_data, indent=4)
        else:
            formatted_body = "No body in request"
            return JsonResponse({"status": "failed"})
    except json.JSONDecodeError:
        formatted_body = request.body.decode('utf-8')

    shop = "247c21-78.myshopify.com"
    session = shopify.Session(shop, "unstable", "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") #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
    shopify.ShopifyResource.activate_session(session)

    sub_id = body_data.get('subscription_contract_id')
    order_id = body_data.get('order_id')
    customer_id = get_sub_contract_customer(sub_id)

    products_per_month = get_customer_metafield(customer_id, "deet", "products_per_month") 
    products_per_month = products_per_month if products_per_month else {"value":1}

    freq = get_customer_metafield(customer_id, "deet", "sub_frequency")
    freq = freq if freq else {"value":1}

    skipped = get_customer_metafield(customer_id, "deet", "skipped_months")
    skipped = skipped if skipped else {"value":1}

    case_each_month = get_customer_metafield(customer_id, "deet", "case_each_month")
    case_each_month = case_each_month if case_each_month else False
    
    update_subscription_product_based_on_calendar_record(sub_id, products_per_month["value"])

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
    add_tag_to_order(order_id)

    if case_each_month == "true":
        add_product_to_order(order_id, 0, "CASE", "CASE")

    return JsonResponse({"status": "success"})

def view_functions(request):

    shop = "247c21-78.myshopify.com"
    session = shopify.Session(shop, "unstable", "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") #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
    shopify.ShopifyResource.activate_session(session)

    query = """
        query {
            shopifyFunctions(first: 25) {
                nodes {
                    app {
                        title
                    }
                    apiType
                    title
                    id
                }
            }
        }

    """
    response = shopify.GraphQL().execute(query)
    response_data = json.loads(response)

    return JsonResponse(response_data)

def add_functions(request, function_id):

    shop = "247c21-78.myshopify.com"
    session = shopify.Session(shop, "unstable", "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") #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
    shopify.ShopifyResource.activate_session(session)

    query = """
        mutation cartTransformCreate($functionId: String!) {
            cartTransformCreate(functionId: $functionId) {
                cartTransform {
                    functionId
                    id
                    blockOnFailure
                }
                userErrors {
                field
                message
                }
            }
        }

    """

    variables = {
        "blockOnFailure":"true",
        "functionId":f"{function_id}"
    }
    response = shopify.GraphQL().execute(query, variables=variables)
    response_data = json.loads(response)

    return JsonResponse(response_data)

def view_selling_plan_groups(request):

    query = """
query sellingPlanGroups {
  sellingPlanGroups(first: 100) {
    edges {
      node {
        id
        name
        merchantCode
        appId
        description
        options
        position
        createdAt
        sellingPlans(first: 100) {
          edges {
            node {
              id
            }
          }
        }
        productVariants(first: 100) {
          edges {
            node {
              id
            }
          }
        }
        summary
        products(first: 100) {
          edges {
            node {
              id
            }
          }
        }
      }
    }
  }
}
"""

    shop = "247c21-78.myshopify.com"
    session = shopify.Session(shop, "unstable", "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") #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
    shopify.ShopifyResource.activate_session(session)

    response = shopify.GraphQL().execute(query)
    response_data = json.loads(response)

    return JsonResponse(response_data)

@csrf_exempt
def update_product_sub_price(request):

    headers = {header: value for header, value in request.headers.items()}
    formatted_headers = json.dumps(headers, indent=4)

    # Extract and format body
    try:
        if request.body:
            body_data = json.loads(request.body)
            formatted_body = json.dumps(body_data, indent=4)
        else:
            formatted_body = "No body in request"
            return JsonResponse({"status": "failed"})
    except json.JSONDecodeError:
        formatted_body = request.body.decode('utf-8')

    shop = "247c21-78.myshopify.com"
    session = shopify.Session(shop, "unstable", "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") #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
    shopify.ShopifyResource.activate_session(session)

    product_id = body_data.get('id')

    variant_id = get_products_subscription_variant_id(product_id)
    premium_value = get_variants_premium_value(variant_id)

    sub_price = 14 + premium_value

    return JsonResponse(update_product_variant_price(variant_id, sub_price))

    

def test_customer_orders(request, customer_id):

    shop = "247c21-78.myshopify.com"
    session = shopify.Session(shop, "unstable", "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") #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
    shopify.ShopifyResource.activate_session(session)

    variant_id = get_products_subscription_variant_id(customer_id)
    premium_value = get_variants_premium_value(variant_id)

    print("variant_id: ",variant_id)
    print("premium_value: ",premium_value)

    sub_price = 14 + premium_value

    return JsonResponse(update_product_variant_price(variant_id, sub_price))

@csrf_exempt
def delete_selling_plan_view(request):
    if request.method == 'POST':
        form = DeleteSellingPlanForm(request.POST)
        if form.is_valid():
            selling_plan_group_id = form.cleaned_data['selling_plan_group_id']
            selling_plan_id = form.cleaned_data['selling_plan_id']
            response = delete_selling_plan(selling_plan_group_id, [selling_plan_id])
            return  JsonResponse(response)
    else:
        form = DeleteSellingPlanForm()

    return render(request, 'subscriptions/delete_selling_plan.html', {'form': form})

@csrf_exempt
def view_all_selling_plans(request):

    return JsonResponse(view_selling_plans())

@csrf_exempt
def delete_selling_plan_group_view(request, selling_plan_group_id):

    return JsonResponse(delete_selling_plan_group(selling_plan_group_id))

def embed_overview(request):

    def count_sub_statuses(subs):
        # Extract the subscription contracts
        contracts = subs['data']['subscriptionContracts']['edges']

        status_count = {
            "ACTIVE":0,
            "CANCELLED":0,
            "PAUSED":0,
            "ALL":0
        }

        for contract in contracts:
            node = contract['node']
           
            status_count[node['status']] += 1
            status_count["ALL"] += 1
            
        return status_count

    shop = "247c21-78.myshopify.com"
    session = shopify.Session(shop, "unstable", "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")
    shopify.ShopifyResource.activate_session(session)

    subs = get_all_subscription_contracts()
    status_count = count_sub_statuses(subs)

    return render(request, 'embed/embed_overview.html', {'status_count': status_count})

@csrf_exempt
def all_sub_products(request):
    data = get_products_and_variants_with_sku_suffix()
    return JsonResponse(data, safe=False)

@csrf_exempt
def handle_failure(request):

    #FailedSubscriptionAttempt.objects.all().delete()

    # Extract and log headers
    headers = {header: value for header, value in request.headers.items()}
    formatted_headers = json.dumps(headers, indent=4)
    print("formatted_headers: ", formatted_headers)

    # Extract and log body
    try:
        if request.body:
            body_data = json.loads(request.body)
            formatted_body = json.dumps(body_data, indent=4)
            print("formatted_body: ", formatted_body)
        else:
            return JsonResponse({"status": "failed", "message": "No body in request"})
    except json.JSONDecodeError:
        formatted_body = request.body.decode('utf-8')
        return JsonResponse({"status": "failed", "message": "Invalid JSON body"})

    # Handle failed payment
    subscription_id = body_data.get("admin_graphql_api_subscription_contract_id")

    if subscription_id:
        try:
            with transaction.atomic():
                attempt, created = FailedSubscriptionAttempt.objects.select_for_update().get_or_create(
                    subscription_id=subscription_id,
                    status='pending',
                    defaults={'next_retry': timezone.now() + timezone.timedelta(minutes=RETRY_INTERVAL_MINUTES)}
                )

                if not created:
                    attempt.schedule_next_retry()
                    print("ATTEMPT: ",attempt)
                else:
                    record = FailedSubscriptionAttempt.objects.get(subscription_id=subscription_id)
                    print("CREATED: ",record)

        except IntegrityError:
            print(f"Failed to handle the subscription ID {subscription_id} due to a database error.")

    else:
        print("NO SUB")

    return JsonResponse({"status": "received"})

