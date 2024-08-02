import requests
import json

class ShopifyGraphQLClient:
    
    def __init__(self, shop, access_token):
        self.shop = shop
        self.access_token = access_token
        self.endpoint = f"https://{shop}.myshopify.com/api/2024-04/graphql.json"
        self.headers = {
            "Content-Type": "application/json",
            "X-Shopify-Storefront-Access-Token": access_token,
        }

    def execute(self, query, variables=None):
        payload = {
            "query": query,
            "variables": variables
        }
        
        response = requests.post(self.endpoint, headers=self.headers, data=json.dumps(payload))

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Query failed to run by returning code of {response.status_code}. {query}")