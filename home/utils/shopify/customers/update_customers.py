import json
import shopify
from datetime import datetime

from .get_customers import *

from ..general.customer import *
from ..general.subscriptions import *
from ..general.metafields import *

def add_customer_metafield(cusotmer_id, namespace, key, value, value_type):

    cusotmer_id = format_customer_id(cusotmer_id)

    query = """
    mutation customerUpdate($input: CustomerInput!) {
      customerUpdate(input: $input) {
        customer {
          metafields(first: 100) {
            edges {
              node {
                namespace
                key
                value
              }
            }
          }
        }
        userErrors {
          field
          message
        }
      }
    }
    """
    
    variables = {
        "input": {
            "id": cusotmer_id,
            "metafields": [
                {
                    "namespace": namespace,
                    "key": key,
                    "value": value,
                    "type": value_type
                }
            ]
        }
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    print("ADD META RESP: ",response)
    return json.loads(response)

def update_customer_metafield(customer_id, metafield_id, value):

    customer_id = format_customer_id(customer_id)
    metafield_id = format_metafield_id(metafield_id)

    query = """
    mutation customerUpdate($input: CustomerInput!) {
      customerUpdate(input: $input) {
        customer {
          metafields(first: 100) {
            edges {
              node {
                namespace
                key
                value
              }
            }
          }
        }
        userErrors {
          field
          message
        }
      }
    }
    """
    
    variables = {
        "input": {
            "id": customer_id,
            "metafields": [
                {
                    "id":metafield_id,
                    "value": value
                }
            ]
        }
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    return json.loads(response)

def update_customer_contact_details(customer_id, first_name, last_name, email, phone):

    customer_id = format_customer_id(customer_id)

    query = """
        mutation customerUpdate($input: CustomerInput!) {
        customerUpdate(input: $input) {
            userErrors {
            field
            message
            }
            customer {
            id
            firstName
            lastName
            }
        }
        }
    """

    variables = {
        "input": {
            "id": customer_id,
            "firstName": first_name,
            "lastName": last_name,
            "email":email,
            }
        }
    
    response = shopify.GraphQL().execute(query, variables=variables)
    print("response: ",response)
    return json.loads(response)

def customer_skip_months(customer_id, shop, n):

    from ...dbs.calendarEvent import get_most_recent_future_events
    from ..subscriptions.update_subs import skip_n_billing_cycles, update_subscription_product_based_on_calendar_record, set_next_billing_date

    if customer_id:

        subs = get_customer_subscription_contracts(customer_id)
        
        keys = list(subs.keys())
        i = 0
        first_active = None

        # Iterate with while loop
        while i < len(keys):
            key = keys[i]
            subscription = subs[key]
            
            if subscription['status'] == 'ACTIVE':
                first_active = key
                break
            
            i += 1
        
        else:
            return {'error':'no subscriptions'}


        if not first_active:
            return {'error':'no active subscriptions'}
        else:

            records = get_most_recent_future_events(customer_id, shop)
            skip_n_billing_cycles(first_active, records, n)

            skip = get_customer_metafield(customer_id, "deet", "skipped_months")
            print("skip: ",skip)
            
            if not skip:
                r = add_customer_metafield(customer_id, "deet", "skipped_months", str(n), "number_decimal")
            else:
                r = update_customer_metafield(customer_id, skip["id"], str(n) )

            products_per_month = get_customer_metafield(customer_id, "deet", "products_per_month")

            freq = get_customer_metafield(customer_id, "deet", "sub_frequency")
            subs = get_first_active_sub(get_customer_subscription_contracts(customer_id))

            today = datetime.today()
            if today.month == 12: 

                if float(freq["value"]) > 1:
                    next_month = 1 + float(freq["value"]) + float(n)
                else:
                    next_month = 1 + float(n)

                year = today.year + 1
            else:

                if float(freq["value"]) > 1:
                    next_month = today.month + 1 + float(freq["value"]) + float(n)
                else:
                    next_month = today.month + 1 + float(n)

                year = today.year

            next_billing_date = datetime(year, int(next_month), 10)
            print("next_billing_date: ",next_billing_date)
            set_next_billing_date(subs["id"], next_billing_date)

        return {'done':r}
    
def customer_case_each_month(customer_id, value=None):
    
    sub = is_customer_subscribed(customer_id)

    if sub != False:

        case_each_month = get_customer_metafield(customer_id, "deet", "case_each_month")

        if not case_each_month:

            if value:
                r = add_customer_metafield(customer_id, "deet", "case_each_month", value, "boolean")
            else:
                r = add_customer_metafield(customer_id, "deet", "case_each_month", "false", "boolean")


        else:
            
            if case_each_month["value"] == "false" and not value:
                r = update_customer_metafield(customer_id, case_each_month["id"], "true")
            elif value: 
                r = update_customer_metafield(customer_id, case_each_month["id"], value) 
            else:
                r = update_customer_metafield(customer_id, case_each_month["id"], "false") 

            return r  
    
    else:
        return sub
    
def customer_commited_months(customer_id, months):

    from ..subscriptions.update_subs import update_subscription_min_billing_cycles

    sub = is_customer_subscribed(customer_id)

    if sub != False:
        
        commited_months = get_customer_metafield(customer_id, "deet", "commited_months")
        sub_id = get_first_active_sub(get_customer_subscription_contracts(customer_id))

        if not commited_months:
            r = add_customer_metafield(customer_id, "deet", "commited_months", str(months), "number_decimal" )
        else:
            r = update_customer_metafield(customer_id, commited_months["id"], str(months))

        r = update_subscription_min_billing_cycles(sub_id, months)

        return r 
    
    else:
        return sub
    
def customer_products_per_month(customer_id, products):

    sub = is_customer_subscribed(customer_id)

    if sub != False:
        
        products_per_month = get_customer_metafield(customer_id, "deet", "products_per_month")

        if not products_per_month:
            r = add_customer_metafield(customer_id, "deet", "products_per_month", str(products), "number_decimal")
        else:
            r = update_customer_metafield(customer_id, products_per_month["id"], str(products))
            
        return r

    else:
        return {"status":"failed",
                "reason":"User Is Not Subscribed"}
    
def customer_sub_frequency(customer_id, frequency):

    from ..subscriptions.update_subs import update_subscription_interval_count

    sub = is_customer_subscribed(customer_id)

    if sub != False:
        
        sub_frequency = get_customer_metafield(customer_id, "deet", "sub_frequency")
        sub_id = get_first_active_sub(get_customer_subscription_contracts(customer_id))

        if not sub_frequency:
            r = add_customer_metafield(customer_id, "deet", "sub_frequency", str(frequency), "number_decimal")
        else:
            r = update_customer_metafield(customer_id, sub_frequency["id"], str(frequency))

        r = update_subscription_interval_count(sub_id["id"], frequency)

        return r 

    else:
        return sub


    