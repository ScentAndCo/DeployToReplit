import json
import shopify

from ..general.customer import *
from ..general.subscriptions import *
from ..general.product import *
from ..general.metafields import *

def add_product_metafield(product_id, namespace, key, value, value_type):

    product_id = format_product_id(product_id)

    query = """
    mutation productUpdate($input: ProductInput!) {
      productUpdate(input: $input) {
        product {
          metafields(first: 100) {
            edges {
              node {
                namespace
                key
                value
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
        "input": {
            "id": product_id,
            "metafields": [
                {
                    "namespace": namespace,
                    "key": key,
                    "value": value,
                    "type": value_type
                }
            ]
        }
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    return json.loads(response)

def update_product_metafield(product_id, metafield_id, value):

    product_id = format_product_id(product_id)
    metafield_id = format_metafield_id(metafield_id)

    query = """
    mutation productUpdate($input: ProductInput!) {
      productUpdate(input: $input) {
        product {
          metafields(first: 100) {
            edges {
              node {
                namespace
                key
                value
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
        "input": {
            "id": product_id,
            "metafields": [
                {
                    "id":metafield_id,
                    "value": value
                }
            ]
        }
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    return json.loads(response)

def update_product_variant_price(variant_id, price):
    
    variant_id = format_product_variant_id(variant_id)

    print("variant_id: ",variant_id)

    query = """
    mutation updateProductVariantPrice($input: ProductVariantInput!) {
      productVariantUpdate(input: $input) {
        productVariant {
          id
          price
        }
        userErrors {
          message
          field
        }
      }
    }
    """

    variables = {
        "input":{
            "price":f"{price}",
            "id":variant_id
        }
    }

    print("variables: ",variables)

    response = shopify.GraphQL().execute(query, variables=variables)
    return json.loads(response)