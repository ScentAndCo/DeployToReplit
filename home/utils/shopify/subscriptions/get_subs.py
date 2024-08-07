import json
import shopify
from datetime import datetime

from ..general.subscriptions import *
from ..general.product import *

def get_subscription_draft(draft_id):

    draft_id = format_subscriptionDraft_id(draft_id)

    query = """
    query {
      subscriptionDraft(id: "%s") {
        id
        status
        nextBillingDate
        customer {
          id
          email
          firstName
          lastName
        }
        billingPolicy {
          interval
          intervalCount
          anchors {
            day
            month
            type
          }
        }
        deliveryPolicy {
          interval
          intervalCount
          anchors {
            day
            month
            type
          }
        }
        lines(first: 10) {
          edges {
            node {
              id
              title
              quantity
            }
          }
        }
      }
    }
    """ % draft_id

    response = shopify.GraphQL().execute(query)
    response_data = json.loads(response)

    print("Subscription Draft Response:", response_data)
    return response_data

def get_subscription_plan(plan_id):

    plan_id = format_sellingPlanGroup_id(plan_id)

    query = """
    query {
      sellingPlanGroup(id: "%s") {
        id
        name
        options
        sellingPlans(first: 10) {
          edges {
            node {
              id
              name
              description
            }
          }
        }
      }
    }
    """ % plan_id

    response = shopify.GraphQL().execute(query)
    response_data = json.loads(response)

    print("Subscription Plan Response:", response_data)
    return response_data

def get_all_subscription_contracts():
    query = """
    {
      subscriptionContracts(first: 100) {
        edges {
          node {
            id
            status
            nextBillingDate
            lastPaymentStatus
            billingPolicy {
              interval
              intervalCount
              minCycles
              maxCycles
              anchors {
                day
                month
                cutoffDay
                type
              }
            }
            customer {
              id
              firstName
              lastName
              email
            }
            lines(first: 10) {
              edges {
                node {
                  id
                  title
                  variantTitle
                  variantId
                  productId
                  quantity
                  currentPrice {
                    amount
                    currencyCode
                  }
                }
              }
            }
            deliveryPrice {
              amount
              currencyCode
            }
          }
        }
      }
    }
    """
    
    response = shopify.GraphQL().execute(query)
    response_data = json.loads(response)

    return response_data

def get_subscription_billing_attempt(billing_attempt_id):
    
    billing_attempt_id = format_subscriptionBillingAttempt_id(billing_attempt_id)

    # query = """
    # query findBillingAttempt($subscriptionBillingAttempt: ID!) {
    #   subscriptionBillingAttempt(id: $subscriptionBillingAttempt) {
    #     id
    #     nextActionUrl
    #     idempotencyKey
    #     ready
    #     order {
    #       id
    #     }
    #     subscriptionContract {
    #       id
    #     }
    #     originTime
    #     completedAt
    #     errorMessage
    #     errorCode
    #   }
    # }
    # """

    query = """
    {
      subscriptionBillingAttempts(first:10){
        edges{
          node {
            id 
            createdAt
            errorCode
            errorMessage
            ready
            order{
              id
              capturable
            }
            subscriptionContract{
              id
            }

          }
        }
      }
    }
    """
    
    # variables = {
    #     "subscriptionBillingAttempt": billing_attempt_id
    # }
    
    # response = shopify.GraphQL().execute(query, variables=variables)
    response = shopify.GraphQL().execute(query)
    response_data = json.loads(response)
    
    print("Subscription Billing Attempt Response:", response_data)
    return response_data

def get_billing_cycles(contract_id):
    
    contract_id = format_subscriptionContract_id(contract_id)
     #DateTime!
    query = """
    query subscriptionBillingCycles($contractId: ID!, $startDate: Int!, $endDate: Int!) {
      subscriptionBillingCycles(first: 250, contractId: $contractId, billingCyclesIndexRangeSelector: {startIndex: $startDate, endIndex: $endDate}) {
        edges {
          node {
            billingAttemptExpectedDate
            cycleIndex
            status
            cycleStartAt
            cycleEndAt
            skipped

            sourceContract{
              id
              customer{
                id
              }
            }
          }
        }
      }
    }
    """
    
    variables = {
        "contractId": contract_id,
        "startDate": 1,#"2000-01-01T00:00:00Z",  # Example start date in ISO 8601 format
        "endDate": 10#datetime.utcnow().isoformat() + "Z"  # Current date and time
    }
    
    response = shopify.GraphQL().execute(query, variables=variables)
    response_data = json.loads(response)
    
    if 'errors' in response_data:
        print("Errors:", response_data['errors'])
        return []
    
    #print("Billing Cycles Response:", response_data)
    return response_data.get('data', {}).get('subscriptionBillingCycles', {}).get('edges', [])

def get_subscription_line_item(contract_id):
    
    contract_id = format_subscriptionContract_id(contract_id)

    query = """
    query findContract($subscriptionContractId: ID!) {
      subscriptionContract(id: $subscriptionContractId) {
        id
        status
        nextBillingDate
        lineCount
        lines(first: 100) {
          edges {
            node {
              id
              title
              variantTitle
              quantity
              variantId
              sku
              currentPrice {
                amount
                currencyCode
              }

              variantImage{
                altText
                url
              }
            }
          }
        }
      }
    }
    """

    variables = {
        "subscriptionContractId": contract_id,
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    response_data = json.loads(response)

    response_data = parse_subscription_lines(response_data)

    return response_data

def get_sub_contract_customer(contract_id):
    
    def get_customer_id(response):
      try:
          customer_id = response['data']['subscriptionContract']['customer']['id']
          return customer_id
      except (KeyError, TypeError):
          return None
    
    contract_id = format_subscriptionContract_id(contract_id)

    query = """
    query findContract($subscriptionContractId: ID!) {
      subscriptionContract(id: $subscriptionContractId) {
        id
        customer{
          id
        }
      }
    }
    """

    variables = {
        "subscriptionContractId": contract_id,
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    response_data = json.loads(response)
    
    return get_customer_id(response_data)

def get_sub_contract_billing_data(contract_id):
    
    def get_billing_policy(response):
        try:
            return response['data']['subscriptionContract']['billingPolicy']
        except:
            return None
    
    contract_id = format_subscriptionContract_id(contract_id)

    query = """
    query findContract($subscriptionContractId: ID!) {
      subscriptionContract(id: $subscriptionContractId) {
        id
        billingPolicy{
          interval
          intervalCount
          maxCycles
          minCycles
        }
      }
    }
    """

    variables = {
        "subscriptionContractId": contract_id,
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    response_data = json.loads(response)
    
    return get_billing_policy(response_data)

def get_sub_line_variant_ids(contract_id):
    
    def extract_variant_ids(data):
      variant_ids = []
      try:
          edges = data['data']['subscriptionContract']['lines']['edges']
          for edge in edges:
              variant_id = edge['node'].get('variantId')
              line_id = edge['node'].get('id')
              if variant_id:
                  variant_ids.append({"variant_id": variant_id, "line_id": line_id})
      except KeyError:
          pass
      return variant_ids
    
    contract_id = format_subscriptionContract_id(contract_id)

    query = """
    query findContract($subscriptionContractId: ID!) {
      subscriptionContract(id: $subscriptionContractId) {
        id
        lines(first: 100){
          edges{
            node{
              id
              variantId
            }
          }
        }
      }
    }
    """

    variables = {
        "subscriptionContractId": contract_id
    }
    
    response = shopify.GraphQL().execute(query, variables=variables)
    response_data = json.loads(response)

    return extract_variant_ids(response_data)

def get_basic_sub_info(contract_id):
    
    def unwrap_subscription_info(subscription_data):
      # Extract the main data
      data = subscription_data.get('data', {})
      subscription_contract = data.get('subscriptionContract', {})

      # Extract the subscription information
      subscription_info = {
          'id': subscription_contract.get('id'),
          'createdAt': subscription_contract.get('createdAt'),
          'lastPaymentStatus': subscription_contract.get('lastPaymentStatus'),
          'nextBillingDate': subscription_contract.get('nextBillingDate'),
          'status': subscription_contract.get('status'),
          'updatedAt': subscription_contract.get('updatedAt')
      }

      return subscription_info
    
    contract_id = format_subscriptionContract_id(contract_id)

    query = """
    query findContract($subscriptionContractId: ID!) {
      subscriptionContract(id: $subscriptionContractId) {
        id
        createdAt
        lastPaymentStatus
        nextBillingDate
        status
        updatedAt
      }
    }
    """

    variables = {
        "subscriptionContractId": contract_id
    }
    
    response = shopify.GraphQL().execute(query, variables=variables)
    response_data = json.loads(response)

    return unwrap_subscription_info(response_data)

def view_selling_plans():
    
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
              sellingPlans(first: 1) {
                edges {
                  node {
                    id
                  }
                }
              }
              productVariants(first: 1) {
                edges {
                  node {
                    id
                  }
                }
              }
              summary
              products(first: 1) {
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

    response = shopify.GraphQL().execute(query)
    response_data = json.loads(response)

    return response_data

def view_specific_sub_contract_func(sub_id):
    
    sub_id = format_subscriptionContract_id(sub_id)
    
    session = shopify.Session("247c21-78.myshopify.com", "unstable", "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")
    shopify.ShopifyResource.activate_session(session)

    query = """
    query findContract($subscriptionContractId: ID!) {
      subscriptionContract(id: $subscriptionContractId) {
        id
        status
        nextBillingDate
        deliveryMethod{
          SubscriptionDeliveryMethodShipping{
            address{
              address1
              address2
              city
              company
              country
              countryCode
              firstName
              lastName
              name
              phone
              province
              provinceCode
              zip
            }
          }
        }
      }
    }
    """

    variables = {
        "subscriptionContractId":sub_id
    }

    response = shopify.GraphQL().execute(query, variables)
    response_data = json.loads(response)

    return response_data