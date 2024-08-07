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
    print("metafield Resp: ",response)
    return json.loads(response)

def update_product_variant_price(variant_id, price):
    
    variant_id = format_product_variant_id(variant_id)

    #print("variant_id: ",variant_id)

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

    #print("variables: ",variables)

    response = shopify.GraphQL().execute(query, variables=variables)
    return json.loads(response)

def add_or_update_product_metafield(product_id, namespace, key, value, metafield_type):
    def find_metafield(data, namespace, key):
        metafields = data.get("data", {}).get("product", {}).get("metafields", {}).get("edges", [])
        for metafield in metafields:
            metafield_node = metafield.get("node", {})
            if metafield_node.get("namespace") == namespace and metafield_node.get("key") == key:
                return metafield_node
        return None

    # GraphQL query to fetch product metafields with namespace filter
    query = """
    query ($id: ID!, $namespace: String!) {
        product(id: $id) {
            metafields(first: 250, namespace: $namespace) {
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
    """

    variables = {"id": product_id, "namespace": namespace}
    response = shopify.GraphQL().execute(query, variables)
    response_data = json.loads(response)
    existing_metafield = find_metafield(response_data, namespace, key)

    if metafield_type.startswith("list"):
        value = json.dumps(value)
    else:
        value = str(value)

    if value == "":
        value = " "

    metafield_input = {
        "namespace": namespace,
        "key": key,
        "value": value,
        "type": metafield_type
    }

    if existing_metafield:
        metafield_input["id"] = existing_metafield["id"]

    # Use productUpdate mutation to update the product with metafield
    mutation = """
    mutation($input: ProductInput!) {
        productUpdate(input: $input) {
            product {
                id
                metafields(first: 250) {
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
            "metafields": [metafield_input]
        }
    }

    response = shopify.GraphQL().execute(mutation, variables)
    response_data = json.loads(response)

    return response_data

def update_all_product(product_data):
    
    session = shopify.Session("247c21-78.myshopify.com", "unstable", "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")
    shopify.ShopifyResource.activate_session(session)
    
    def update_product(id ,product_data):
        
        from .get_products import get_product_variant_id_via_sku, get_product_details, find_product_metafield_id

        query = """
          mutation updateProduct($input: ProductInput!, $media:[CreateMediaInput!]) {
            productUpdate(input:$input, media:$media){
                  product {
                    id
                  }
            }
          }
        """

        name = product_data["Name"]
        brand = product_data["Brand"]
        sku = product_data["SKU"]
        premium_value = product_data["Premium Value"]
        full_bottle_price = product_data["Full Bottle Price"]

        tags = ["premium-all", product_data["Level 1 Catagory"]]

        subscription_id = get_product_variant_id_via_sku(sku+"_S")
        one_time_id = get_product_variant_id_via_sku(sku+"_OT")
        full_bottle_id = get_product_variant_id_via_sku(sku+"_FB")
        
        sub_price = 14 + int(premium_value)
        one_time_price = 19 + int(premium_value)

        update_product_variant_price(subscription_id, sub_price)
        update_product_variant_price(one_time_id, one_time_price)
        update_product_variant_price(full_bottle_id, full_bottle_price)

        if int(premium_value) > 0:
            tags.append("premium-yes")
        else:
            tags.append("premium-no")

        if product_data["Show In Shop"]:
            tags.append("shop")

        if product_data["Show In Subscription"]:
            tags.append("subscription")

        if not name.startswith(brand+" "):
          name = f"{brand} {name}"

        print('product_data["Fragrance Family"]: ',product_data["Fragrance Family"])

        add_or_update_product_metafield(id, "data", "gender", product_data["Gender"].split(', '), "list.single_line_text_field")
        add_or_update_product_metafield(id, "pricing", "premium_value", premium_value, "number_integer")
        add_or_update_product_metafield(id, "data", "fragrance_family",product_data["Fragrance Family"], "single_line_text_field")
        add_or_update_product_metafield(id, "data", "longevity", product_data["Longevity"], "single_line_text_field")
        add_or_update_product_metafield(id, "data", "notes", [product_data["Note 1"], product_data["Note 2"], product_data["Note 3"]], "list.single_line_text_field")
        add_or_update_product_metafield(id, "data", "season", product_data["Season"], "single_line_text_field")
        add_or_update_product_metafield(id, "data", "occasion", product_data["Occasion"], "single_line_text_field")
        add_or_update_product_metafield(id, "data", "stockcode", product_data["sg_stockcode"], "single_line_text_field")

        product_input = {"input":{
            "id":id,
            "title":name,
            "vendor":product_data["Brand"],
            "descriptionHtml":product_data["Short Desc"],
            "productType":product_data["Level 1 Catagory"],
            "tags":tags        
        },
          # "media":[{
          #     "alt":name,
          #     "mediaContentType":"IMAGE",
          #     "originalSource":product_data["Image"]
          # }]}
        }

        response = shopify.GraphQL().execute(query, product_input)
    
    for key in product_data:
      print("UPDATING: ",key)
      update_product(key, product_data[key])

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

def create_products(create_data):
    
    session = shopify.Session("247c21-78.myshopify.com", "unstable", "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")
    shopify.ShopifyResource.activate_session(session)

    from .get_products import get_channels
    
    def get_variant_id_with_sku_suffix_s(response_json):
      try:
          data = json.loads(response_json)
          product_variants = data.get("data", {}).get("productVariantsBulkCreate", {}).get("productVariants", [])
          
          for variant in product_variants:
              sku = variant.get("sku", "")
              if "_S" in sku:
                  return variant.get("id", "")
          
          return ""
      except json.JSONDecodeError:
          return ""

    def get_publication_id(response_json, publication_name):
      try:
          data = json.loads(response_json)
          publications = data.get("data", {}).get("publications", {}).get("edges", [])
          for publication in publications:
              node = publication.get("node", {})
              if node.get("name") == publication_name:
                  return node.get("id", "")
          return ""
      except json.JSONDecodeError:
          return ""

    def extract_product_id(response_json):
      try:
          data = json.loads(response_json)
          return data.get("data", {}).get("productCreate", {}).get("product", {}).get("id", "")
      except json.JSONDecodeError:
          return ""
      
    def publish_product(product_id, publish_id):
        
        query = """
          mutation publishablePublish($id: ID!, $input: [PublicationInput!]!) {
            publishablePublish(id: $id, input: $input) {
              publishable {
                availablePublicationsCount {
                  count
                }
                resourcePublicationsCount {
                  count
                }
              }
              shop {
                publicationCount
              }
              userErrors {
                field
                message
              }
            }
          }
        """

        variables = {
            "id":product_id,
            "input": {
                "publicationId": publish_id
                }
        }

        shopify.GraphQL().execute(query, variables)
    
    def create_product(product_data):
      query = """
      mutation createProduct($input: ProductInput!, $media:[CreateMediaInput!]) {
        productCreate(input:$input, media:$media){
            product {
            id
            options {
                id
                name
                position
                values
                optionValues {
                  id
                  name
                  hasVariants
                }
              }
            }
        }
      }
      """

      name = product_data["Name"]
      brand = product_data["Brand"]
      premium_value = product_data["Premium Value"]

      tags = ["premium-all", product_data["Level 1 Catagory"]]
      
      if int(premium_value) > 0:
          tags.append("premium-yes")
      else:
          tags.append("premiuim-no")

      if product_data["Show In Shop"]:
          tags.append("shop")

      if product_data["Show In Subscription"]:
            tags.append("subscription")

      if not name.startswith(brand+" "):
          name = f"{brand} {name}"

      variables = {
          "input":{
              "title":name,
              "vendor":brand,
              "descriptionHtml":product_data["Short Desc"],
              "productType":product_data["Level 1 Catagory"],
              "tags":tags,
              "productOptions":{
                  "name":"Duration",
                  "position":1,
                  "values":[
                      {
                          "name":"subscription"
                      },
                      {
                          "name":"one time"
                      },
                      {
                          "name":"full bottle"
                      }
                  ]
              }  
          },
          "media":[{
              "alt":name,
              "mediaContentType":"IMAGE",
              "originalSource":product_data["Image"]
          }]
      }

      response = shopify.GraphQL().execute(query, variables)
      #print("CREATE RESP: ",response)
      productID = extract_product_id(response)

      add_or_update_product_metafield(productID, "data", "gender", product_data["Gender"].split(', '), "list.single_line_text_field")
      add_or_update_product_metafield(productID, "pricing", "premium_value", premium_value, "number_integer")
      add_or_update_product_metafield(productID, "data", "fragrance_family",product_data["Fragrance Family"], "single_line_text_field")
      add_or_update_product_metafield(productID, "data", "longevity", product_data["Longevity"], "single_line_text_field")
      add_or_update_product_metafield(productID, "data", "notes", [product_data["Note 1"], product_data["Note 2"], product_data["Note 3"]], "list.single_line_text_field")
      add_or_update_product_metafield(productID, "data", "season", product_data["Season"], "single_line_text_field")
      add_or_update_product_metafield(productID, "data", "occasion", product_data["Occasion"], "single_line_text_field")
      add_or_update_product_metafield(productID, "data", "stockcode", product_data["sg_stockcode"], "single_line_text_field")
      pubID = get_publication_id(get_channels(), "Online Store")
      publish_product(productID, pubID)

      return productID
    
    def create_variants(product_id, product_data):
        
        query = """
          mutation productVariantsBulkCreate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
            productVariantsBulkCreate(productId: $productId, variants: $variants, strategy:REMOVE_STANDALONE_VARIANT) {
              product {
                id
              }
              productVariants {
                id
                sku
              }
            }
          }
        """

        premium_value = product_data["Premium Value"]
        if premium_value == "":
            premium_value = 0

        full_bottle_price = product_data["Full Bottle Price"]
        sub_price = 14 + int(premium_value)
        one_time_price = 19 + int(premium_value)

        sku = product_data["SKU"]
        subscription_sku = sku+"_S"
        one_time_sku = sku+"_OT"
        full_bottle_sku = sku+"_FB"

        variables = {
            "productId":product_id,
            "variants":[
                {
                    "price":str(sub_price),
                    "inventoryItem":{
                        "sku":subscription_sku,
                        "tracked":False
                    },
                    "optionValues":{
                        "name":"subscription",
                        "optionName":"Duration"
                    }
                },
                {
                    "price":str(one_time_price),
                    "inventoryItem":{
                        "sku":one_time_sku,
                        "tracked":False
                    },
                    "optionValues":{
                        "name":"one time",
                        "optionName":"Duration"
                    }
                },
                {
                    "price":str(full_bottle_price),
                    "inventoryItem":{
                        "sku":full_bottle_sku,
                        "tracked":False
                    },
                    "optionValues":{
                        "name":"full bottle",
                        "optionName":"Duration"
                    }
                }
            ]
            
        }
        response = shopify.GraphQL().execute(query, variables)
        print("VAR RESP: ",response)
        sub_id = get_variant_id_with_sku_suffix_s(response)
        add_product_to_selling_plan_group("76967739725", [sub_id])
        

    for product in create_data:  
      productID = create_product(create_data[product])
      create_variants(productID, create_data[product])

# lets just make sure 

