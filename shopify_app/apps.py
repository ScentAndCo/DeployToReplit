from django.apps import AppConfig
import os


class ShopifyAppConfig(AppConfig):
    name = 'shopify_app'
    # Replace the API Key and Shared Secret with the one given for your
    # App by Shopify.
    #
    # To create an application, or find the API Key and Secret, visit:
    # - for private Apps:
    #     https://${YOUR_SHOP_NAME}.myshopify.com/admin/api
    # - for partner Apps:
    #     https://www.shopify.com/services/partners/api_clients
    #
    # You can ignore this file in git using the following command:
    #   git update-index --assume-unchanged shopify_settings.py
    SHOPIFY_API_KEY = os.environ.get('SHOPIFY_API_KEY', "c5f5be49ab02f9b799c27d949006f426")
    SHOPIFY_API_SECRET = os.environ.get('SHOPIFY_API_SECRET', "4130c89c7ca1d23738b02372114bb054")

    # API_VERSION specifies which api version that the app will communicate with
    SHOPIFY_API_VERSION = os.environ.get('SHOPIFY_API_VERSION', 'unstable')

    # See http://api.shopify.com/authentication.html for available scopes
    # to determine the permisssions your app will need.
    SHOPIFY_API_SCOPE = os.environ.get('SHOPIFY_API_SCOPE', 'read_products,write_products,read_orders,write_orders,read_customers,write_customers,read_own_subscription_contracts,write_own_subscription_contracts,read_customer_payment_methods,write_cart_transforms,read_cart_transforms,write_order_edits,read_order_edits').split(',')
