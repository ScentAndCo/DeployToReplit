import json
import shopify
from datetime import datetime, timedelta

from ..general.customer import *



def create_subscription_draft(customer_id, billing_policy, delivery_method, currency_code="GBP", next_billing_date=None):
    
    if next_billing_date is None:
        tomorrow = datetime.now() + timedelta(days=1)
        next_billing_date = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0).isoformat()
    else:
        next_billing_date = next_billing_date.isoformat()

    customer_id = format_customer_id(customer_id)
    payment_ids = get_payment_ids_for_customer(customer_id)

    mutation = """
    mutation subscriptionContractCreate($input: SubscriptionContractCreateInput!) {
      subscriptionContractCreate(input: $input) {
        draft {
          id
          status
          nextBillingDate
        }
        userErrors {
          field
          message
        }
      }
    }
    """

    for payment_method_id in payment_ids:
      variables = {
          "input": {
              "contract": {
                  "billingPolicy": billing_policy,
                  "deliveryMethod": delivery_method,
                  "paymentMethodId": payment_method_id,
                  "status": "ACTIVE",  # Ensure status is not empty
                  "deliveryPolicy": {
                      "interval": billing_policy['interval'],  # Add delivery policy details
                      "intervalCount": billing_policy['intervalCount']
                  },
                  "deliveryPrice":0.0
              },
              "currencyCode": currency_code,
              "customerId": customer_id,
              "nextBillingDate": next_billing_date
          }
      }

      response = shopify.GraphQL().execute(mutation, variables=variables)
      response_data = json.loads(response)

      print("Created Response:", response_data,"\n")

      if not response_data.get('data', {}).get('subscriptionContractCreate', {}).get('userErrors', []):
          print("Response:", response_data)
          return response_data

    # If all payment methods fail
    return response_data

def create_subscription_sc_selling_group(resources):
    
    query = """
    mutation createSellingPlanGroup($input: SellingPlanGroupInput!){
      sellingPlanGroupCreate(input: $input){
        sellingPlanGroup {
          id
          sellingPlans(first: 1) {
            edges{
              node{
                id
              }
            }
          }
        }
      }
    }
    """

    variables = {
        "input":{
            "name":"MONTHLY SUBSCRIPTION - £14",
            "merchantCode":"sc-sub-plan",
            "options":["1 month"],
            "sellingPlansToCreate":{
                "name":"MONTHLY SUBSCRIPTION - £14",
                "options":"1 month",
                "category":"SUBSCRIPTION",
                "billingPolicy":{
                    "recurring":{
                        "interval":"MONTH",
                        "intervalCount":1,
                    }
                },
                "deliveryPolicy":{
                    "recurring":{
                        "interval":"MONTH",
                        "intervalCount":1,
                    }
                }
                
            },
        },
        "resources": resources
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    response_data = json.loads(response)

    return response_data

