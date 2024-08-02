import json
import shopify

def format_customer_id(customer_id):
    if type(customer_id) != str or customer_id.isdigit():
        customer_id = str(customer_id)
        return f"gid://shopify/Customer/{customer_id}"
    return customer_id

def get_payment_ids_for_customer(customer_id, amount:int=10):

    customer_id = format_customer_id(customer_id)

    query = """
    {
      customer(id: "%s") {
      firstName
        paymentMethods(first: 5 showRevoked:true) {
          edges {
            node {
              id
            }
          }
        }
      }
    }
    """ % customer_id

    response = shopify.GraphQL().execute(query)
    response_data = json.loads(response)
    
    payment_method_ids = [
        edge['node']['id']
        for edge in response_data.get('data', {}).get('customer', {}).get('paymentMethods', {}).get('edges', [])
    ]

    return response_data