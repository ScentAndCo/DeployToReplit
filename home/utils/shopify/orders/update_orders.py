import json
import shopify

from ..general.order import *

def add_tag_to_order(order_id, tag_text:str="renewal"):

    order_id = format_order_id(order_id)

    mutation = """
    mutation orderUpdate($input: OrderInput!) {
      orderUpdate(input: $input) {
        order {
          id
          tags
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
            "id": order_id,
            "tags": [tag_text]
        }
    }
    
    response = shopify.GraphQL().execute(mutation, variables=variables)
    response_data = json.loads(response)
    
    print("Order Update Response:", response_data)
    return response_data

def put_order_into_calculated(order_id):
    
    def get_calculated_order_id(response):
      """
      Extracts the id of the calculated order from the JSON response.

      Parameters:
      response (str): The JSON response as a string.

      Returns:
      str: The id of the calculated order if present, otherwise None.
      """
      if 'data' in response_data and 'orderEditBegin' in response_data['data']:
          if 'calculatedOrder' in response_data['data']['orderEditBegin']:
              return response_data['data']['orderEditBegin']['calculatedOrder'].get('id')
      return None
    
    order_id = format_order_id(order_id)

    mutation = """
    mutation orderEditBegin($id: ID!) {
  orderEditBegin(id: $id) {
    calculatedOrder {
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
      "id": order_id,
    }
    
    response = shopify.GraphQL().execute(mutation, variables=variables)
    response_data = json.loads(response)
    
    print("Order cal Response:", response_data,"\n\n")
    return get_calculated_order_id(response_data)

def commit_calculated_order(order_id):
    
    order_id = format_calculated_order_id(order_id)

    mutation = """
mutation orderEditCommit($id: ID!) {
  orderEditCommit(id: $id) {
    order {
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
      "id": order_id,
    }
    
    response = shopify.GraphQL().execute(mutation, variables=variables)
    response_data = json.loads(response)
    
    print("Order commit Response:", response_data, "\n\n")

def add_product_to_order(order_id, price, sku, title):

    order_id = format_calculated_order_id(put_order_into_calculated(order_id))

    mutation = """
mutation orderEditAddCustomItem($id: ID!, $price: MoneyInput!, $quantity: Int!, $title: String!, $sku: String!) {
  orderEditAddCustomItem(id: $id, price: $price, quantity: $quantity, title: $title, sku:$sku) {
    calculatedLineItem {
      id
    }
    calculatedOrder {
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
      "id": order_id,
      "price": {
        "amount": price,
        "currencyCode": "GBP"
      },
      "quantity": 1,
      "requiresShipping": "true",
      "sku": sku,
      "title": title,
    }
    
    response = shopify.GraphQL().execute(mutation, variables=variables)
    response_data = json.loads(response)
    
    print("Order Update Response:", response_data,"\n\n")

    commit_calculated_order(order_id)
    return response_data
