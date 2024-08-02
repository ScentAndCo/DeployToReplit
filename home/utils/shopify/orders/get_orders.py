import json
import shopify

from ..general.order import *
from ..general.customer import *

def get_new_sub_data_from_order(order_id):

    def extract_order_info(data):
        order_info = {}

        # Extract shipping address information
        shipping_address = data['data']['order']['shippingAddress']
        for key, value in shipping_address.items():
            order_info[key] = value

        # Extract variant IDs with title "decantable"
        line_items = data['data']['order']['lineItems']['edges']
        variant_ids = []
        for item in line_items:
            variant = item['node']['variant']
            if variant['title'].lower() == 'subscription':
                variant_ids.append(variant['id'])
        
        order_info['variant_ids'] = variant_ids

        return order_info


    order_id = format_order_id(order_id)

    query = """
    query getOrder($id: ID!) {

        order(id: $id) {
            id

            shippingAddress{
                address1
                address2
                city
                company
                countryCodeV2
                firstName
                lastName
                phone
                provinceCode
                zip
            }

            lineItems(first:100){
                edges{
                    node{
                        variant{
                            id
                            price
                            title
                        }
                    }
                }
            }
        }
    }
    """

    variables = {
        "id": order_id
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    response_data = json.loads(response)

    return extract_order_info(response_data)

def get_customer_orders(customer_id):

    #customer_id = format_customer_id(customer_id)

    query = """
    query {

        orders(first: 100, query:"customer_id:%s", sortKey:CREATED_AT) {
            edges{
                node{
                    id
                    name
                    createdAt
                }
            }
        }
    }
    """%customer_id


    response = shopify.GraphQL().execute(query)
    response_data = json.loads(response)

    return response_data