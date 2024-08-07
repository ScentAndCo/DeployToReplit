import json
import shopify

from ..general.customer import *
from ..general.subscriptions import *
from ..general.metafields import *

def get_customer_details(customer_id):
    customer_id = format_customer_id(customer_id)

    query = """
    query getCustomer($customerId: ID!) {
      customer(id: $customerId) {
        id
        firstName
        lastName
        email
        phone
        numberOfOrders
        amountSpent {
          amount
          currencyCode
        }
        createdAt
        updatedAt
        note
        verifiedEmail
        productSubscriberStatus
        validEmailAddress
        tags
        lifetimeDuration
        defaultAddress {
          formattedArea
          address1
        }
        addresses {
          address1
        }
        image {
          src
        }
        canDelete

        subscriptionContracts(first: 100){
            edges {
                node {
                    id
                    status
                }
            }
        
        }

        metafields(first: 100) {
            edges {
              node {
                id
                namespace
                key
                value
                type
              }
            }
          }
      }
    }
    """

    variables = {
        "customerId": customer_id
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    response_data = json.loads(response)

    return response_data.get('data', {}).get('customer', {})

def get_customer_subscription_contracts(customer_id):

    customer_id = format_customer_id(customer_id)

    query = """
    query getCustomer($customerId: ID!) {
      customer(id: $customerId) {
        id
        productSubscriberStatus
        subscriptionContracts(first: 100){
            edges {
                node {
                    id
                    status
                    lastPaymentStatus
                    nextBillingDate
                }
            }
        
        }
      }
    }
    """

    variables = {
        "customerId": customer_id
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    response_data = json.loads(response)

    return parse_subscription_data(response_data.get('data', {}).get('customer', {}))

def is_customer_subscribed(customer_id):
    result = get_first_active_sub(get_customer_subscription_contracts(customer_id))

    if result == False:
        return False
    else:
        return True

def get_customer_metafield_data(customer_id):
    
    customer_id = format_customer_id(customer_id)

    query = """
    query getCustomer($customerId: ID!) {
      customer(id: $customerId) {
        id
        metafields(first: 100) {
            edges {
              node {
                id
                namespace
                key
                value
                type
              }
            }
          }
      }
    }
    """

    variables = {
        "customerId": customer_id
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    response_data = json.loads(response)

    try:
      return parse_metafield_data(response_data.get('data', {}).get('customer', {}))
    except:
        return {}

def get_customer_metafield(customer_id, namespace, key):
    return find_metafield_by_namespace_and_key(get_customer_metafield_data(customer_id), namespace, key)

