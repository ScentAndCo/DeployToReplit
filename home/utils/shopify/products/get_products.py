import json
import shopify

from ..general.customer import *
from ..general.subscriptions import *
from ..general.product import *

from ...googleSheets.GoogleSheet import GoogleSheet

def get_product_details(product_id):

    product_id = format_product_id(product_id)

    query = """
    query productQuery($id: ID!) {
      product(id: $id) {
        id
        title
        description
        createdAt
        updatedAt
        vendor
        productType
        tags
        totalInventory
        variants(first: 100) {
          edges {
            node {
              id
              title
              sku
              price
              inventoryQuantity
            }
          }
        }
        images(first: 10) {
          edges {
            node {
              src
              altText
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
              description
              type
              ownerType
              createdAt
              updatedAt
            }
          }
        }
      }
    }
    """
    
    variables = {
        "id": product_id
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    return json.loads(response)

def get_product_variant_details(product_id):

    product_id = format_product_variant_id(product_id)

    query = """
    query productQuery($productId: ID!){
      productVariant(id: $productId) {
        id
        title
        displayName
        metafield(key:"premium_value", namespace:"pricing"){
          namespace
          value
          type
        }

        image{
          altText
          url
        }

        product{
          vendor
          metafield(key:"premium_value", namespace:"pricing"){
            namespace
            value
            type
          }

          featuredImage{
            altText
            url
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

    return response_data

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

def is_product_varaint_sub(product_id):
    
    def is_decantable(data):
      try:
          title = data['data']['productVariant']['title']
          return title == 'subscription'
      except KeyError:
          return False

    product_id = format_product_variant_id(product_id)

    query = """
    query productQuery($productId: ID!){
      productVariant(id: $productId) {
        id
        title
      }
    }
    """
    
    variables = {
        "productId": product_id
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    response_data =  json.loads(response)

    return is_decantable(response_data)

def is_product_varaint_fee(product_id):
    
    def is_fee(data):
      try:
          title = data['data']['productVariant']['displayName'].lower()
          print("title: ",title)
          return 'fee' in title
      except KeyError:
          return False

    product_id = format_product_variant_id(product_id)

    query = """
    query productQuery($productId: ID!){
      productVariant(id: $productId) {
        id
        title
        displayName
      }
    }
    """
    
    variables = {
        "productId": product_id
    }

    response = shopify.GraphQL().execute(query, variables=variables)
    response_data =  json.loads(response)

    return is_fee(response_data)

def get_product_variant_id_via_sku(sku):
    
    def get_first_product_variant_id(data):
      try:
          return data['data']['productVariants']['edges'][0]['node']['id']
      except (KeyError, IndexError):
          return None
    
    query = """
      {
        productVariants(first: 1, query: "sku:%s") {
          edges {
            node {
              id
            }
          }
        }
      }
  """% sku

    response = shopify.GraphQL().execute(query)
    response_data =  json.loads(response)

    return get_first_product_variant_id(response_data)

def get_products_subscription_variant_id(product_id):
    
    def find_variant_with_s(data):
        # Extract the product variants
        variants = data.get("data", {}).get("product", {}).get("variants", {}).get("edges", [])
        
        # Iterate through each variant
        for variant in variants:
            sku = variant.get("node", {}).get("sku", "").upper()
            if sku.endswith("_S"):
                return variant.get("node", {}).get("id")
        
        return None
    
    product_id = format_product_id(product_id)

    query = """
      query ($id:ID!){
        product(id: $id) {
          variants(first: 3){
            edges{
              node{
                sku
                id
              }
            }
          }
        }
      }
    """

    variables = {
        "id": product_id
    }

    response = shopify.GraphQL().execute(query, variables)
    response_data = json.loads(response)
    id = find_variant_with_s(response_data)
    
    return id

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


def get_products_and_variants_with_sku_suffix():
    
    def transform_data_to_dict(data):

      result = {}
      for row in data:
          sku = row.get('SKU')  # Replace 'SKU' with the actual column name for SKUs in your sheet
          if sku:
              result[sku] = row
      return result
    
    from ..subscriptions.update_subs import add_product_to_selling_plan_group

    gs = GoogleSheet("home\creds.json", "S&C Stock v3", worksheet_name="Var Products")
    print("GETTING RECORDS")
    data = gs.read_all_records()

    print("TRANSFORMING")
    data = transform_data_to_dict(data)
    
    # Set up Shopify session
    session = shopify.Session("247c21-78.myshopify.com", "unstable", "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")
    shopify.ShopifyResource.activate_session(session)

    # GraphQL query to fetch products and variants
    query = """
    {
        products(first: 250) {
            edges {
                node {
                    id
                    title
                    variants(first: 250) {
                        edges {
                            node {
                                id
                                sku
                                title
                            }
                        }
                    }
                }
            }
            pageInfo {
                hasNextPage
                endCursor
            }
        }
    }
    """

    def fetch_all_products(query):
        all_products = []
        has_next_page = True
        while has_next_page:
            print("Query: ",query)
            result = shopify.GraphQL().execute(query)
            data = json.loads(result)

            print("DATA: ", json.dumps(data, indent=4),"\n")
            products = data['data']['products']['edges']
            all_products.extend(products)
            has_next_page = data['data']['products']['pageInfo']['hasNextPage']
            if has_next_page:
                last_cursor = data['data']['products']['pageInfo']['endCursor']              
                query = """
                {
                    products(first: 250, after:"%s") {
                        edges {
                            node {
                                id
                                title
                                variants(first: 250) {
                                    edges {
                                        node {
                                            id
                                            sku
                                            title
                                        }
                                    }
                                }
                            }
                        }
                        pageInfo {
                            hasNextPage
                            endCursor
                        }
                    }
                }
                """%last_cursor
        return all_products

    # Fetch all products using GraphQL
    print("FETCHING")
    all_products = fetch_all_products(query)

    # Find variants with SKU containing "_S"
    print("CREATING all_variants_with_s")
    all_variants_with_s = []
    for product in all_products:
        product_node = product['node']
        for variant in product_node['variants']['edges']:
            variant_node = variant['node']
            if variant_node['sku'] and "_S" in variant_node['sku']:
                all_variants_with_s.append({
                    'product_id': product_node['id'],
                    'variant_id': variant_node['id'],
                    'sku': variant_node['sku'],
                    'title': variant_node['title']
                })

    # Construct result as a dictionary
    result_dict = {
        "variants_with_s": all_variants_with_s
    }

    print("ADDING DATA")
    for n in all_variants_with_s:
        
        id = n['product_id']
        var_id = n['variant_id']
        sku = n['sku'].replace("_S", "")
        print(f"WORKING ON {sku}")
        
        row = data[sku]
        try:
          premium = int(row["Premium Value"])
        except:
            premium = 0
    
        is_premium = False
        if premium and premium > 0:
            is_premium = True
            
        add_or_update_product_metafield(id, "pricing", "premium_value", premium, "number_integer")
        add_or_update_product_metafield(id, "data", "fragrance_family",row["Fragrance Family"], "single_line_text_field")
        add_or_update_product_metafield(id, "data", "longevity", row["Longevity"], "single_line_text_field")
        add_or_update_product_metafield(id, "data", "notes", [row["Note 1"], row["Note 2"], row["Note 3"]], "list.single_line_text_field")
        add_or_update_product_metafield(id, "data", "season", row["Season"], "single_line_text_field")
        add_or_update_product_metafield(id, "data", "occasion", row["Occasion"], "single_line_text_field")
        add_or_update_product_metafield(id, "data", "is_premium", is_premium, "boolean")
        add_or_update_product_metafield(id, "data", "gender", row["Gender"].split(', '), "list.single_line_text_field")

        add_product_to_selling_plan_group("76967739725", [var_id])
        

      

    # Convert result to JSON for better readability
    result_json = json.dumps(result_dict, indent=4)
    return json.loads(result_json)
