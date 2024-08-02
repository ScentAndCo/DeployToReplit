import json 
import shopify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import hashlib

class GoogleSheet:
    
    def __init__(self, json_keyfile_path, sheet_name, worksheet_name="Sheet1"):
        self._json_keyfile_path = json_keyfile_path
        self._sheet_name = sheet_name
        self._worksheet_name = worksheet_name
        self._scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        self._client = self.authenticate()
        self._sheet = self.get_sheet()
        self._rows_cache = self._build_rows_cache()

    def authenticate(self):
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(self._json_keyfile_path, self._scope)
            client = gspread.authorize(creds)
            return client
        except Exception as e:
            print(f"Error during authentication: {e}")
            return None

    def get_sheet(self):
        try:
            sheet = self._client.open(self._sheet_name).worksheet(self._worksheet_name)
            return sheet
        except gspread.SpreadsheetNotFound:
            print("Spreadsheet not found.")
        except gspread.WorksheetNotFound:
            print(f"Worksheet '{self._worksheet_name}' not found.")
        except gspread.GSpreadException as e:
            print(f"Error accessing spreadsheet: {e}")
        return None

    def _build_rows_cache(self):
        try:
            rows = self._sheet.get_all_values()
            rows_cache = {}
            for idx, row in enumerate(rows):
                row_hash = self._hash_row(row)
                rows_cache[row_hash] = idx + 1
            return rows_cache
        except gspread.GSpreadException as e:
            print(f"Error building rows cache: {e}")
            return {}

    def _hash_row(self, row):
        row_str = ','.join(row)
        return hashlib.md5(row_str.encode('utf-8')).hexdigest()

    def add_row(self, row_values, allow_duplicates=True):
        try:
            if not allow_duplicates:
                row_hash = self._hash_row(row_values)
                if row_hash in self._rows_cache:
                    row_number = self._rows_cache[row_hash]
                    self.update_row(row_number, row_values)
                    return

            self._sheet.append_row(row_values)
            print(f"Row added: {row_values}")

            # Update cache
            if not allow_duplicates:
                row_hash = self._hash_row(row_values)
                self._rows_cache[row_hash] = len(self._rows_cache) + 1

        except gspread.GSpreadException as e:
            print(f"Error adding row: {e}")

    def update_row(self, row_number, values):
        try:
            for i, value in enumerate(values):
                col = i + 1  # Convert index to 1-based column number
                self._sheet.update_cell(row_number, col, value)
            print(f"Row {row_number} updated with values: {values}")
        except gspread.GSpreadException as e:
            print(f"Error updating row {row_number}: {e}")

    def bulk_update_range(self, start_row, start_col, data):
        try:
            if isinstance(start_col, str):
                start_col = self._convert_column_to_index(start_col)
                
            end_row = start_row + len(data) - 1
            end_col = start_col + len(data[0]) - 1
            cell_range = f"{self._convert_to_A1_notation(start_row, start_col)}:{self._convert_to_A1_notation(end_row, end_col)}"
            cell_list = self._sheet.range(cell_range)

            flat_data = [item for sublist in data for item in sublist]
            for cell, value in zip(cell_list, flat_data):
                cell.value = value

            self._sheet.update_cells(cell_list)
            print(f"Bulk updated range: {cell_range}")
        except gspread.GSpreadException as e:
            print(f"Error in bulk updating range: {e}")

    def _convert_to_A1_notation(self, row, col):
        """Convert row and column numbers to A1 notation."""
        letter = ''
        while col > 0:
            col, remainder = divmod(col - 1, 26)
            letter = chr(65 + remainder) + letter
        return f'{letter}{row}'

    def read_all_records(self):
        try:
            return self._sheet.get_all_records()
        except gspread.GSpreadException as e:
            print(f"Error reading records: {e}")
            return None

    def read_cell(self, row, col):
        try:
            col = self._convert_column_to_index(col)
            return self._sheet.cell(row, col).value
        except gspread.GSpreadException as e:
            print(f"Error reading cell: {e}")
            return None

    def delete_row(self, index):
        try:
            self._sheet.delete_row(index)
            print(f"Row deleted at index {index}")
        except gspread.GSpreadException as e:
            print(f"Error deleting row: {e}")

    def create_new_sheet(self, title, rows=1000, cols=26):
        try:
            new_sheet = self._client.create(title)
            new_sheet.resize(rows, cols)
            print(f"New sheet created with title: {title}")
            return new_sheet
        except gspread.GSpreadException as e:
            print(f"Error creating new sheet: {e}")
            return None

    def delete_sheet(self, title):
        try:
            sheet = self._client.open(title)
            self._client.del_spreadsheet(sheet.id)
            print(f"Sheet deleted with title: {title}")
        except gspread.GSpreadException as e:
            print(f"Error deleting sheet: {e}")

    def _convert_column_to_index(self, col):
        if isinstance(col, int):
            return col
        elif isinstance(col, str):
            col = col.upper()
            index = 0
            for char in col:
                index = index * 26 + (ord(char) - ord('A') + 1)
            return index
        else:
            raise ValueError("Column should be either an integer or a string representing a column letter.")

    def get_row(self, row_number):
        try:
            row_values = self._sheet.row_values(row_number)
            return row_values
        except gspread.GSpreadException as e:
            print(f"Error getting row {row_number}: {e}")
            return None

    def find_last_row_with_data(self, col):
        try:
            col_index = self._convert_column_to_index(col)
            col_values = self._sheet.col_values(col_index)
            last_row_with_data = len(col_values) - next((i for i, v in enumerate(reversed(col_values)) if v), len(col_values))
            return last_row_with_data
        except gspread.GSpreadException as e:
            print(f"Error finding last row with data in column {col}: {e}")
            return None

    # Getters and Setters
    @property
    def json_keyfile_path(self):
        return self._json_keyfile_path

    @json_keyfile_path.setter
    def json_keyfile_path(self, path):
        self._json_keyfile_path = path
        self._client = self.authenticate()
        self._sheet = self.get_sheet()

    @property
    def sheet_name(self):
        return self._sheet_name

    @sheet_name.setter
    def sheet_name(self, name):
        self._sheet_name = name
        self._sheet = self.get_sheet()
        self._rows_cache = self._build_rows_cache()  # Rebuild the cache when the sheet is changed

    @property
    def worksheet_name(self):
        return self._worksheet_name

    @worksheet_name.setter
    def worksheet_name(self, name):
        self._worksheet_name = name
        self._sheet = self.get_sheet()
        self._rows_cache = self._build_rows_cache()  # Rebuild the cache when the sheet is changed


def format_selling_group_plan_id(id):
    if type(id) != str or id.isdigit():
        id = str(id)
        return f"gid://shopify/SellingPlanGroup/{id}"
    return id

def format_product_variant_id(product_id):
    if type(product_id) != str or product_id.isdigit():
        product_id = str(product_id)
        return f"gid://shopify/ProductVariant/{product_id}"
    return product_id

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
                    tags
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
            #print("Query: ",query)
            result = shopify.GraphQL().execute(query)
            data = json.loads(result)

            #print("DATA: ", json.dumps(data, indent=4),"\n")
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
                                tags
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
        if 'fragrance' in product_node['tags']:
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
        
        try:
            row = data[sku]
            try:
                premium = int(float(row["Premium Value"]))
            except Exception as e:
                print("PREMIUM EXCPECTION: ",e)
                premium = 0
        
            is_premium = ["exclusively"]
            if premium and premium > 0:
                is_premium = ["inclusively", "all"]
                
            add_or_update_product_metafield(id, "pricing", "premium_value", premium, "number_integer")
            
            if row["Fragrance Family"] != "":
                add_or_update_product_metafield(id, "data", "fragrance_family",row["Fragrance Family"], "single_line_text_field")
            
            if row["Longevity"] != "":
                add_or_update_product_metafield(id, "data", "longevity", row["Longevity"], "single_line_text_field")
            
            if row["Note 1"] != "" or row["Note 2"] != "" or row["Note 3"] != "":
                add_or_update_product_metafield(id, "data", "notes", [row["Note 1"], row["Note 2"], row["Note 3"]], "list.single_line_text_field")
            
            if row["Season"] != "":
                add_or_update_product_metafield(id, "data", "season", row["Season"], "single_line_text_field")
            
            if row["Occasion"] != "":
                add_or_update_product_metafield(id, "data", "occasion", row["Occasion"], "single_line_text_field")

            add_or_update_product_metafield(id, "data", "is_premium_data", is_premium, "list.single_line_text_field")
            add_or_update_product_metafield(id, "data", "gender", row["Gender"].split(', '), "list.single_line_text_field")

            add_product_to_selling_plan_group("76967739725", [var_id])
        except:
            continue
        

      

    # Convert result to JSON for better readability
    result_json = json.dumps(result_dict, indent=4)
    return json.loads(result_json)

get_products_and_variants_with_sku_suffix()