from ..general.product import *
from ..general.cart import *
from ..general.graphql import *

def get_line_item_id_for_variant(variant_id, cart_id):

    variant_id = format_product_variant_id(variant_id)
    cart_id = format_cart_id(cart_id)

    query = """
    query cartQuery($id:ID!){
        cart(id:$id) {
            id
            lines(first:100){
                edges{
                    node{
                        id
                        merchandise{
                            ... on ProductVariant{
                                id
                            }
                        }
                    }
                }
            }
        }
    }
    """

    variables = {
        "id":cart_id
    }

    a = ShopifyGraphQLClient("quickstart-cfb56ba2", "00174722951c688ed6f6919ca96df8c0")
    resp = a.execute(query, variables=variables)
    
    if 'data' in resp and 'cart' in resp['data'] and 'lines' in resp['data']['cart']:
        for edge in resp['data']['cart']['lines']['edges']:
            node = edge['node']
            if 'merchandise' in node and node['merchandise']['id'] == variant_id:
                return node['id']
            
    return None

