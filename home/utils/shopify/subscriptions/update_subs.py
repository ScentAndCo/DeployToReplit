import json
import shopify
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from ..general.subscriptions import *
from ..general.product import *
from ..general.utils import *

from ..orders.update_orders import *

from ..subscriptions.get_subs import *

from ..products.get_products import *

from ...dbs.calendarEvent import *

from ....models import *

from decimal import Decimal

def decimal_to_str(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError

def add_line_item_to_draft(draft_id, variant_id, quantity=1, premium_value=0):

    draft_id = format_subscriptionDraft_id(draft_id)
    variant_id = format_product_variant_id(variant_id)

    mutation = """
    mutation subscriptionDraftLineAdd($draftId: ID!, $input: SubscriptionLineInput!) {
      subscriptionDraftLineAdd(draftId: $draftId, input: $input) {
        draft {
          id
        }
        lineAdded {
          id
          title
          quantity
          currentPrice{
            amount
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
        "draftId": draft_id,
        "input": {
            "productVariantId": variant_id,
            "quantity": quantity,
            "currentPrice": 14 + premium_value,
        }
    }
    
    response = shopify.GraphQL().execute(mutation, variables=variables)
    response_data = json.loads(response)

    print("Add Line Item Response:", response_data,"\n")
    return response_data

def commit_subscription_draft(draft_id):

    draft_id = format_subscriptionDraft_id(draft_id)

    mutation = """
    mutation subscriptionDraftCommit($draftId: ID!) {
      subscriptionDraftCommit(draftId: $draftId) {
        contract {
          id
          status
          nextBillingDate
          createdAt
        }
        userErrors {
          field
          message
        }
      }
    }
    """

    variables = {
        "draftId": draft_id
    }

    response = shopify.GraphQL().execute(mutation, variables=variables)
    response_data = json.loads(response)

    print("Commit Response:", response_data,"\n")
    return response_data

def add_subscription_plan(input, resources):
    mutation = """
    mutation createSellingPlanGroup($input: SellingPlanGroupInput!, $resources: SellingPlanGroupResourceInput) {
        sellingPlanGroupCreate(input: $input, resources: $resources) {
            sellingPlanGroup {
                id
                sellingPlans(first: 1) {
                    edges {
                        node {
                            id
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
        "input": input,
        "resources": resources
    }

    response = shopify.GraphQL().execute(mutation, variables=variables)
    response_data = json.loads(response)
    
    print("Add Subscription Plan Response:", response_data)
    return response_data

def delete_selling_plan(selling_plan_group_id, selling_plan_ids):

  selling_plan_group_id = format_selling_group_plan_id(selling_plan_group_id)

  for n in range (0, len(selling_plan_ids)):
      selling_plan_ids[n] = format_sellingPlan_id(selling_plan_ids[n])
  
  mutation = """
    mutation sellingPlanGroupUpdate($id: ID!, $input: SellingPlanGroupInput!) {
      sellingPlanGroupUpdate(id: $id, input: $input) {
        deletedSellingPlanIds
        sellingPlanGroup {
          id
          sellingPlans(first: 1) {
            edges {
              node {
                id
                metafields(first: 1) {
                  edges {
                    node {
                      id
                      namespace
                      key
                      value
                    }
                  }
                }
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
      "id":selling_plan_group_id,
      "input":{
         "sellingPlansToDelete":selling_plan_ids
      }
  }

  response = shopify.GraphQL().execute(mutation, variables=variables)
  response_data = json.loads(response)

  return response_data

def subscription_contract_product_change(contract_id, line_id, variant_id, price):

    contract_id = format_subscriptionContract_id(contract_id)
    line_id = format_subscriptionLine_id(line_id)
    variant_id = format_product_variant_id(variant_id)

    mutation = """
    mutation($contractId: ID!, $lineId: ID!, $variantId: ID!, $price: Decimal!) {
      subscriptionContractProductChange(subscriptionContractId: $contractId, lineId: $lineId, input: {productVariantId: $variantId, currentPrice: $price}) {
        contract {
          id
          updatedAt
        }
        lineUpdated {
          id
          currentPrice {
            amount
          }
          variantId
        }
        userErrors {
          field
          message
          code
        }
      }
    }
    """
    
    variables = {
        "contractId": contract_id,
        "lineId": line_id,
        "variantId": variant_id,
        "price": price
    }

    print("Change sub product variables: ",variables)
    
    response = shopify.GraphQL().execute(mutation, variables=variables)
    response_data = json.loads(response)
    
    print("Subscription Contract Product Change Response:", response_data)
    return response_data

def subscription_contract_product_remove(draft_id, line_id):

    draft_id = format_subscriptionDraft_id(draft_id)
    line_id = format_subscriptionLine_id(line_id)

    mutation = """
    mutation subscriptionDraftLineRemove($draftId: ID!, $lineId: ID!) {
      subscriptionDraftLineRemove(draftId: $draftId, lineId: $lineId) {

        draft {
          id
        }

    userErrors {
      field
      message
    }
  }
}
    """
    
    variables = {
        "draftId": draft_id,
        "lineId": line_id,
    }
    
    response = shopify.GraphQL().execute(mutation, variables=variables)
    response_data = json.loads(response)

    return response_data

def create_subscription_billing_attempt(contract_id, index, origin_time=None):
    
    if not origin_time:
      origin_time = (datetime.now()).isoformat()

    contract_id = format_subscriptionContract_id(contract_id)

    mutation = """
    mutation subscriptionBillingAttemptCreate($contractId: ID!, $index: Int!, $originTime: DateTime!, $idempotencyKey:String!) {
      subscriptionBillingAttemptCreate(subscriptionContractId: $contractId, subscriptionBillingAttemptInput: {billingCycleSelector: {index: $index}, idempotencyKey: $idempotencyKey, originTime: $originTime}) {
        subscriptionBillingAttempt {
          id
          ready
          order {
            id
          }
        }
        userErrors {
          field
          message
        }
      }
    }
    """
    unique_value = generate_random_alphanumeric_string(12)
    variables = {
        "contractId": contract_id,
        "index": index,
        "idempotencyKey":unique_value,
        "originTime": origin_time.isoformat()
    }
    
    response = shopify.GraphQL().execute(mutation, variables=variables)
    response_data = json.loads(response)
    
    print("Subscription Billing Attempt Create Response:", response_data)

    if 'subscriptionBillingAttemptCreate' in response_data.get('data', {}):
        billing_attempt = response_data['data']['subscriptionBillingAttemptCreate'].get('subscriptionBillingAttempt')
        if billing_attempt and billing_attempt.get('order'):
            order_id = billing_attempt['order'].get('id')
            if order_id:
                add_subscription_tag_to_order(order_id)
            else:
                print("FINAL HURDLE")
        else:
            print("second HURDLE")
    
    else:
        print("ISSUE")

    return response_data

def set_next_billing_date(contract_id, next_billing_date):
    contract_id = format_subscriptionContract_id(contract_id)
    next_billing_date_iso = next_billing_date.isoformat()  # Convert datetime to ISO format string

    mutation = """
    mutation subscriptionContractSetNextBillingDate($contractId: ID!, $date: DateTime!) {
      subscriptionContractSetNextBillingDate(contractId: $contractId, date: $date) {
        contract {
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
    
    variables = {
        "contractId": contract_id,
        "date": next_billing_date_iso  # Use the ISO format string
    }
    
    response = shopify.GraphQL().execute(mutation, variables=variables)
    response_data = json.loads(response)
    
    #print("Set Next Billing Date Response:", response_data)
    return response_data

def skip_n_billing_cycles(contract_id:str, mostRecentCalendarRecords: list[CalendarEvent], number_to_skip:int=1):
    
    contract_id = format_subscriptionContract_id(contract_id)
    cycles = get_billing_cycles(contract_id)

    count = 0

    for cycle in cycles:
    

      print("count: ",count," number_to_skip: ",number_to_skip)

      if count >= number_to_skip:
          break

      billing_date = cycle["node"]["billingAttemptExpectedDate"]
      date_to_compare = datetime.strptime(billing_date, "%Y-%m-%dT%H:%M:%SZ")
      today = datetime.utcnow()

      if cycle["node"]["status"] != "BILLED" and date_to_compare > today and not cycle["node"]["skipped"]:
        print("SKIPPING")

        mutation = """
        mutation subscriptionBillingCycleSkip($billingCycleInput: SubscriptionBillingCycleInput!) {
          subscriptionBillingCycleSkip(billingCycleInput: $billingCycleInput) {
            billingCycle {
              skipped
            }
            userErrors {
              field
              message
            }
          }
        }
        """

        variables = {
            "billingCycleInput":{
                "contractId":contract_id,
                "selector":{
                    "index":cycle["node"]["cycleIndex"]
                    }
            }
        }
      
        response = shopify.GraphQL().execute(mutation, variables=variables)
        response_data = json.loads(response)
        print(response_data)
        count += 1

      else:
          print("CONDITION NOT MET")    

      
      print("\n")    

    if mostRecentCalendarRecords:
      for record in mostRecentCalendarRecords:

          old_date = record.event_date
          new_date = old_date + relativedelta(months=count)
          record.event_date = new_date
          record.save()    

def update_subscription_product_based_on_calendar_record(contractID:str, product_per_month:int):
    
    contractID = format_subscriptionContract_id(contractID)
    customer_id = get_sub_contract_customer(contractID)
    
    lineData = get_subscription_line_item(contractID)
    if len(lineData) < float(product_per_month):

        print("need products adding")
        
        draft_id = format_subscriptionDraft_id(put_sub_into_update_draft(contractID))

        needed = float(product_per_month) - len(lineData)
        count = 0
        print("need products adding: ",needed)
        while count < needed:
            add_line_item_to_draft(draft_id, format_product_variant_id('48980717142331'), 1)
            count += 1

        commit_subscription_draft(draft_id)

        lineData = get_subscription_line_item(contractID)


    for line_id in lineData:

      record = get_most_recent_future_event(customer_id, "247c21-78.myshopify.com")

      if record:
        print("record: ",record)
        line_id = format_subscriptionLine_id(line_id)

        productID = format_product_variant_id(record.shopify_product_id)
        premium_value = get_variants_premium_value(productID)
        price = 14 + premium_value

        subscription_contract_product_change(contractID, line_id, productID, price)
        
        record.delete()

    return {"DONE"}

def expire_subscription_contract(subscription_contract_id):
    
    subscription_contract_id = format_subscriptionContract_id(subscription_contract_id)
    
    query = """
    mutation subscriptionContractExpire($subscriptionContractId: ID!) {
      subscriptionContractExpire(subscriptionContractId: $subscriptionContractId) {
        contract {
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
    
    variables = {
        "subscriptionContractId": subscription_contract_id
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    return json.loads(response)

def add_variants_to_selling_plan_group(selling_plan_group_id, product_variant_ids):
    

    for n in range(0, len(product_variant_ids)):
        product_variant_ids[n] = format_product_variant_id(product_variant_ids[n])

    query = """
    mutation sellingPlanGroupAddProductVariants($id: ID!, $productVariantIds: [ID!]!) {
      sellingPlanGroupAddProductVariants(id: $id, productVariantIds: $productVariantIds) {
        sellingPlanGroup {
          id
        }
        userErrors {
          field
          message
        }
      }
    }
    """

    variables = {
        "id": selling_plan_group_id,
        "productVariantIds": product_variant_ids
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    return json.loads(response)

def put_sub_into_update_draft(subscription_id):
    
    subscription_id = format_subscriptionContract_id(subscription_id)

    query = """
    mutation subscriptionContractUpdate($contractId: ID!) {
      subscriptionContractUpdate(contractId: $contractId) {
        draft {
          id
        }
        userErrors {
          field
          message
        }
      }
    }
    """

    variables = {
        "contractId": subscription_id,
    }

    response = shopify.GraphQL().execute(query, variables=variables)

    return get_subscription_draft_id(json.loads(response))

def update_subscription_min_billing_cycles(subscription_id, months):
    
    subscription_id = format_subscriptionContract_id(subscription_id)
    billingPolicyDetails = get_sub_contract_billing_data(subscription_id)

    if not billingPolicyDetails:
        
        billingPolicyDetails = {
                "minCycles":int(months),
                "interval":"MONTH",
                "intervalCount":1
            }
        
    else:
        billingPolicyDetails["minCycles"] = int(months)
    
    draft_id = format_subscriptionDraft_id(put_sub_into_update_draft(subscription_id))

    query = """
    mutation subscriptionDraftUpdate($draftId: ID!, $input: SubscriptionDraftInput!) {
    subscriptionDraftUpdate(draftId: $draftId, input: $input) {
      draft {
        id
      }
      userErrors {
        field
        message
      }
    }
  }
    """

    variables = {
        "draftId": draft_id,
        "input":{
            "billingPolicy":billingPolicyDetails,
            "deliveryPolicy":{
                "interval":billingPolicyDetails['interval'],
                "intervalCount":billingPolicyDetails['intervalCount']
            }
        }
    }

    print("variables: ",variables,"\n")

    response = shopify.GraphQL().execute(query, variables=variables)

    return commit_subscription_draft(draft_id)
    
def update_subscription_interval_count(subscription_id, count):
        
    subscription_id = format_subscriptionContract_id(subscription_id)
    billingPolicyDetails = get_sub_contract_billing_data(subscription_id)

    print("billingPolicyDetails: ",billingPolicyDetails)

    if not billingPolicyDetails:
        
        billingPolicyDetails = {
            "interval":"MONTH",
            "intervalCount":int(count)
            }
        
    else:
        billingPolicyDetails["intervalCount"] = int(count)
    
    draft_id = format_subscriptionDraft_id(put_sub_into_update_draft(subscription_id))

    query = """
    mutation subscriptionDraftUpdate($draftId: ID!, $input: SubscriptionDraftInput!) {
    subscriptionDraftUpdate(draftId: $draftId, input: $input) {
      draft {
        id
      }
      userErrors {
        field
        message
      }
    }
  }
    """

    delivery_policy = {
            "interval":"MONTH",
            "intervalCount":int(count)
            }

    variables = {
        "draftId": draft_id,
        "input":{
            "billingPolicy":billingPolicyDetails,
            "deliveryPolicy":delivery_policy
        }
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    print("response: ",response)

    return commit_subscription_draft(draft_id)

def cancel_subscription(contract_id):
    
    contract_id = format_subscriptionContract_id(contract_id)

    query = """
    mutation subscriptionContractCancel($subscriptionContractId: ID!) {
      subscriptionContractCancel(subscriptionContractId: $subscriptionContractId) {
        contract {
          id
        }
        userErrors {
          field
          message
        }
      }
    }
    """

    variables = {
        "subscriptionContractId": contract_id
        }
    
    response = shopify.GraphQL().execute(query, variables=variables)
    print(" Cancel response: ",response)
    return json.loads(response)
     
    
def add_product_to_selling_plan_group(group_plan_id, variant_ids):
    
    for n in range(0, len(variant_ids)):
        variant_ids[n] = format_product_variant_id(variant_ids[n])

    group_plan_id = format_selling_group_plan_id(group_plan_id)
    
    query = """
    mutation sellingPlanGroupAddProductVariants($id: ID!, $productVariantIds: [ID!]!) {
    sellingPlanGroupAddProductVariants(id: $id, productVariantIds: $productVariantIds) {
      sellingPlanGroup {
        id
      }
      userErrors {
        field
        message
      }
    }
  }
    """

    variables = {
        "id":group_plan_id,
        "productVariantIds":variant_ids
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    return json.loads(response)

def update_billing_date(contract_id):
    
    contract_id = format_subscriptionContract_id(contract_id)
    
    query = """
    mutation subscriptionBillingCycleContractEdit($billingCycleInput: SubscriptionBillingCycleInput!) {
      subscriptionBillingCycleContractEdit(billingCycleInput: $billingCycleInput) {
      draft {
        id
      }
      userErrors {
        field
        message
      }
    }
  }
    """

    variables = {
        "billingCycleInput":{
            "contractId":contract_id,
            "selector":{"index":1}
        }
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    response_data = json.loads(response)

    return response_data
    
def delete_selling_plan_group(selling_plan_group_id):
    
    selling_plan_group_id = format_selling_group_plan_id(selling_plan_group_id)

    query = """
    mutation sellingPlanGroupDelete($id: ID!) {
    sellingPlanGroupDelete(id: $id) {
    deletedSellingPlanGroupId
    userErrors {
      field
      message
    }
  }
}
    """

    variables = {
        "id":selling_plan_group_id
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    response_data = json.loads(response)

    return response_data


    