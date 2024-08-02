from ..general.product import *
from ..general.cart import *
from ..general.graphql import *

from ..products.get_products import *
from .get_cart import *

FEES = {
        5:"41022542479454",
        10:"41022542512222",
        15:"41022585536606",
        20:"41022585569374",
        25:"41022585602142"
}

def cart_lines_remove(cart_id, line_ids):

    cart_id = format_cart_id(cart_id)

    mutation = """
    mutation cartLinesRemove($cartId: ID!, $lineIds: [ID!]!) {
    cartLinesRemove(cartId: $cartId, lineIds: $lineIds) {
        cart {
            createdAt

            lines(first:100){
                edges{
                    node{
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
        "cartId": cart_id,
        "lineIds": line_ids
    }

    a = ShopifyGraphQLClient("quickstart-cfb56ba2", "00174722951c688ed6f6919ca96df8c0")
    resp = a.execute(mutation, variables=variables)
    print("\n\n\n\n response: ",resp)
    return resp

def add_cart_fees(cart_id, line_items):

    cart_id = format_cart_id(cart_id)

    fees = []

    for item in line_items:

        sub_product = is_product_varaint_sub(item['id'])

        if sub_product:
            premium_value = get_variants_premium_value(item['id'])
            fee_id = FEES[premium_value]

            for _ in range(0, int(item['quantity'])):
                fees.append({"merchandiseId":format_product_variant_id(fee_id)})

    mutation = """
    mutation cartLinesAdd($cartId: ID!, $lines: [CartLineInput!]!) {
  cartLinesAdd(cartId: $cartId, lines: $lines) {
    cart {
      id
    }
    userErrors {
      field
      message
    }
  }
}
    """

    print("FEES TO ADD: ",fees)
    variables = {
        "cartId": cart_id,
        "lines": fees 
    }

    a = ShopifyGraphQLClient("quickstart-cfb56ba2", "00174722951c688ed6f6919ca96df8c0")
    resp = a.execute(mutation, variables=variables)

    return resp

def remove_fees(cart_id, line_items):
    
    cart_id = format_cart_id(cart_id)

    fees = []

    for item in line_items:

        fee_product = is_product_varaint_fee(item['id'])

        if fee_product:
            print("item: ",item,"\n")
            fees.append(get_line_item_id_for_variant(item['id'], cart_id))

    print("FEES TO REMOVE: ",fees)
    cart_lines_remove(cart_id, fees)