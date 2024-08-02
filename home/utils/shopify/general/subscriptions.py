import re
import json
import shopify


from .product import *

def get_variants_premium_value(product_id):
    
    def extract_value_from_response(response):
      try:
          value = response['data']['productVariant']['product']['metafield']['value']
          return float(value)
      except (KeyError, TypeError, ValueError):
          return 0.0
    
    product_id = format_product_variant_id(product_id)

    query = """
    query productQuery($productId: ID!){
      productVariant(id: $productId) {

        product{
          metafield(key:"premium_value", namespace:"pricing"){
            namespace
            value
            type
          }
        }
      }
    }
    """
    
    variables = {
        "productId": product_id
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    response_data =  json.loads(response)

    value = extract_value_from_response(response_data)

    return value

def get_variants_vendor(product_id):
    
    def extract_value_from_response(response):
      try:
          value = response['data']['productVariant']['product']['vendor']
          return str(value)
      except (KeyError, TypeError, ValueError):
          return ""
    
    product_id = format_product_variant_id(product_id)

    query = """
    query productQuery($productId: ID!){
      productVariant(id: $productId) {

        product{
          vendor
        }
      }
    }
    """
    
    variables = {
        "productId": product_id
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    response_data =  json.loads(response)

    value = extract_value_from_response(response_data)

    return value

def format_subscriptionDraft_id(sub_draft_id):
    if type(sub_draft_id) != str or sub_draft_id.isdigit():
        sub_draft_id = str(sub_draft_id)
        return f"gid://shopify/SubscriptionDraft/{sub_draft_id}"
    return sub_draft_id

def format_sellingPlanGroup_id(plan_id):
    if type(plan_id) != str or plan_id.isdigit():
        plan_id = str(plan_id)
        return f"gid://shopify/SellingPlanGroup/{plan_id}"
    return plan_id

def format_sellingPlan_id(plan_id):
    if type(plan_id) != str or plan_id.isdigit():
        plan_id = str(plan_id)
        return f"gid://shopify/SellingPlan/{plan_id}"
    return plan_id

def format_subscriptionContract_id(plan_id):
    if type(plan_id) != str or plan_id.isdigit():
        plan_id = str(plan_id)
        return f"gid://shopify/SubscriptionContract/{plan_id}"
    return plan_id

def format_subscriptionLine_id(line_id):
    if line_id.find("SubscriptionLine") == -1:
        line_id = str(line_id)
        return f"gid://shopify/SubscriptionLine/{line_id}"
    return line_id

def format_subscriptionBillingAttempt_id(id):
    if type(id) != str or id.isdigit():
        id = str(id)
        return f"gid://shopify/SubscriptionBillingAttempt/{id}"
    return id

def format_selling_group_plan_id(id):
    if type(id) != str or id.isdigit():
        id = str(id)
        return f"gid://shopify/SellingPlanGroup/{id}"
    return id

def parse_subscription_data(subs):

    if subs:
        contracts = subs.get('subscriptionContracts', {}).get('edges', [])
        result = {}
        
        for contract in contracts:
            node = contract['node']
            gid = node['id']
            # Extract numerical part using regex
            numerical_part = re.search(r'\d+$', gid).group()
            # Add to result dictionary
            result[numerical_part] = node
        
        return result

    else:
        return {}

def parse_subscription_lines(data):

    lines = data['data']['subscriptionContract']['lines']['edges']
    parsed_data = {}
    
    for line in lines:
        node = line['node']
        line_id = node['id'].split('/')[-1]  # Extracting the numerical ID part

        premiumValue = get_variants_premium_value(node['variantId'])
        vendor = get_variants_vendor(node['variantId'])

        parsed_data[line_id] = {
            "title": node['title'],
            "variantTitle": node['variantTitle'],
            "quantity": node['quantity'],
            "currentPrice": node['currentPrice'],
            "variationID":node['variantId'],
            "sku":node['sku'],
            "image_url":node['variantImage']['url'],
            "image_alt":node['variantImage']['altText'],
            "premium_value":premiumValue,
            "vendor":vendor
        }
    
    return parsed_data

def get_first_active_sub(subscriptions):
    """
    This function iterates over the provided subscriptions dictionary and returns the first subscription
    that has a status of "ACTIVE". If no active subscriptions are found, it returns None.

    :param subscriptions: A dictionary where keys are subscription IDs and values are subscription details.
    :return: The first active subscription or None if no active subscriptions are found.
    """
    for _, sub_details in subscriptions.items():

        if sub_details.get("status") == "ACTIVE":
            return sub_details
        
    return False

def get_subscription_draft_id(response, src:str='subscriptionContractUpdate'):
      try:
          return response['data'][src]['draft']['id']
      except KeyError:
          return None
      
