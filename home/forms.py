# forms.py
from django import forms
from .models import CalendarEvent

INTERVAL_CHOICES = [
    ('DAY', 'Day'),
    ('WEEK', 'Week'),
    ('MONTH', 'Month'),
    ('YEAR', 'Year'),
]

COUNTRY_CHOICES = [
    ('GB', 'GB'),
]

CURRENCY_CHOICES = [
    ('GBP', 'GBP'),
]

METAFIELD_TYPES = [
    ('number_decimal', 'number_decimal'),
    ('number_integer', 'number_integer'),
    ('multi_line_text_field', 'multi_line_text_field'),
    ('single_line_text_field', 'single_line_text_field'),
    ('url', 'url'),
    ('money', 'money'),
    ('json', 'json')
]

TOPIC_CHOICES = [
        ('APP_UNINSTALLED', 'App Uninstalled'),
        ("CARTS_UPDATE", "CARTS_UPDATE"),
        ("CARTS_CREATE", "CARTS_CREATE"),
        ("ORDERS_CREATE", "ORDERS_CREATE"),
        ("CUSTOMER_PAYMENT_METHODS_CREATE", "CUSTOMER_PAYMENT_METHODS_CREATE"),
        ("CHECKOUTS_CREATE", "CHECKOUTS_CREATE"),
        ("SUBSCRIPTION_CONTRACTS_CREATE", "SUBSCRIPTION_CONTRACTS_CREATE"),
        ("SUBSCRIPTION_BILLING_ATTEMPTS_SUCCESS", "SUBSCRIPTION_BILLING_ATTEMPTS_SUCCESS"),
        ("PRODUCTS_UPDATE", "PRODUCTS_UPDATE"),
        ("SUBSCRIPTION_BILLING_ATTEMPTS_FAILURE", "SUBSCRIPTION_BILLING_ATTEMPTS_FAILURE")
        # Add other topics as needed
    ]

class CalendarEventForm(forms.ModelForm):
    
    class Meta:
        model = CalendarEvent
        fields = ['shopify_product_id', 'shopify_customer_id', 'shopify_shop_domain' ,'event_date']
        widgets = {
            'event_date': forms.DateInput(attrs={'type': 'date'}),
        }

class SubscriptionDraftForm(forms.Form):

    customer_id = forms.CharField(label='Customer ID', max_length=100)
    interval = forms.ChoiceField(label='Interval', choices=INTERVAL_CHOICES)
    interval_count = forms.IntegerField(label='Interval Count', initial=1)
    #max_cycles = forms.IntegerField(label='Max Cycles', initial=12)
    address1 = forms.CharField(label='Address Line 1', max_length=255)
    city = forms.CharField(label='City', max_length=100)
    country_code = forms.ChoiceField(label='Country Code', choices=COUNTRY_CHOICES) 
    first_name = forms.CharField(label='First Name', max_length=50)
    last_name = forms.CharField(label='Last Name', max_length=50)
    province_code = forms.CharField(label='Province Code', max_length=2, initial='NY')
    zip_code = forms.CharField(label='ZIP Code', max_length=20)
    shipping_code = forms.CharField(label='Shipping Code', max_length=100, initial='example-code')
    shipping_title = forms.CharField(label='Shipping Title', max_length=100, initial='Standard Shipping')
    currency_code = forms.ChoiceField(label='Currency', choices=CURRENCY_CHOICES) 
    next_billing_date = forms.DateTimeField(
        label='Next Billing Date',
        initial='2024-06-08T15:50:00Z',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
    #note = forms.CharField(label='Note', max_length=255, required=False)


class AddLineItemForm(forms.Form):
    draft_id = forms.CharField(label='Draft ID', max_length=100)
    variant_id = forms.CharField(label='Variant ID', max_length=100)
    quantity = forms.IntegerField(label='Quantity', initial=1)

class ViewDraftForm(forms.Form):
    draft_id = forms.CharField(label='Draft ID', max_length=100)

class CommitDraftForm(forms.Form):
    draft_id = forms.CharField(label='Draft ID', max_length=100)

class AddSubscriptionPlanForm(forms.Form):
    # name = forms.CharField(label='Name', max_length=100)
    # merchant_code = forms.CharField(label='Merchant Code', max_length=100)
    # option = forms.CharField(label='Option', max_length=100)
    # plan_name = forms.CharField(label='Plan Name', max_length=100)
    # plan_option = forms.CharField(label='Plan Option', max_length=100)
    # interval = forms.ChoiceField(label='Interval', choices=INTERVAL_CHOICES)
    # interval_count = forms.IntegerField(label='Interval Count')
    # base_price = forms.DecimalField(label='Base Price', max_digits=10, decimal_places=2)
    product_id = forms.CharField(label='Product ID', max_length=100)
    # percentage = forms.DecimalField(label='Percentage', max_digits=5, decimal_places=2)
    # delivery_interval = forms.ChoiceField(label='Delivery Interval', choices=INTERVAL_CHOICES)
    # delivery_interval_count = forms.IntegerField(label='Delivery Interval Count')

class ViewSubscriptionPlanForm(forms.Form):
    plan_id = forms.CharField(label='Plan ID', max_length=100)

class SubscriptionContractProductChangeForm(forms.Form):
    contract_id = forms.CharField(label='Contract ID', max_length=100)
    line_id = forms.CharField(label='Line ID', max_length=100)
    variant_id = forms.CharField(label='Variant ID', max_length=100)
    price = forms.DecimalField(label='Price', max_digits=10, decimal_places=2)

class CreateSubscriptionBillingAttemptForm(forms.Form):
    contract_id = forms.CharField(label='Contract ID', max_length=100)
    index = forms.IntegerField(label='Index')
    origin_time = forms.DateTimeField(
        label='Origin Time',
        initial='2024-06-08T15:50:00Z',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )

class ViewSubscriptionBillingAttemptForm(forms.Form):
    billing_attempt_id = forms.CharField(label='Billing Attempt ID', max_length=100)

class CustomerIDForm(forms.Form):
    customer_id = forms.CharField(label='Customer ID', max_length=100)

class NextBillingDateForm(forms.Form):
    contract_id = forms.CharField(label='Subscription Contract ID', max_length=255)
    next_billing_date = forms.DateTimeField(label='Next Billing Date', widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))

class SubscriptionBillingCycleForm(forms.Form):
    contract_id = forms.CharField(label='Subscription Contract ID', max_length=100)

class ProductMetafieldForm(forms.Form):
    product_id = forms.CharField(label='Product ID', max_length=100)
    namespace = forms.CharField(label='Namespace', max_length=100)
    key = forms.CharField(label='Key', max_length=100)
    value = forms.CharField(label='Value', max_length=100)
    value_type = forms.ChoiceField(label='Type', choices=METAFIELD_TYPES)

class CustomerMetafieldForm(forms.Form):
    customer_id = forms.CharField(label='Customer ID', max_length=100)
    namespace = forms.CharField(label='Namespace', max_length=100)
    key = forms.CharField(label='Key', max_length=100)
    value = forms.CharField(label='Value', max_length=100)
    value_type = forms.ChoiceField(label='Type', choices=METAFIELD_TYPES)

class ProductIDForm(forms.Form):
    product_id = forms.CharField(label='Product ID', max_length=100)

class UpdateProductMetafieldForm(forms.Form):
    product_id = forms.CharField(label='Product ID', max_length=100)
    metafield_id = forms.CharField(label='Metafield ID', max_length=100)
    value = forms.CharField(label='New Value', max_length=100)

class UpdateCustomerMetafieldForm(forms.Form):
    customer_id = forms.CharField(label='Customer ID', max_length=100)
    metafield_id = forms.CharField(label='Metafield ID', max_length=100)
    value = forms.CharField(label='New Value', max_length=100)

class ViewSubscriptionContractForm(forms.Form):
    contract_id = forms.CharField(label='Contract ID', max_length=100)

class SubscriptionContractExpireForm(forms.Form):
    subscription_contract_id = forms.CharField(label='Subscription Contract ID', max_length=100)

class SellingPlanGroupAddVariantsForm(forms.Form):
    selling_plan_group_id = forms.CharField(label='Selling Plan Group ID', max_length=100)
    product_variant_ids = forms.CharField(label='Product Variant IDs', widget=forms.Textarea, help_text='Enter product variant IDs separated by commas')

class CustomerSpecificMetafieldForm(forms.Form):
    customer_id = forms.CharField(label='Customer ID', max_length=100)
    namespace = forms.CharField(label='Namespace', max_length=100)
    key = forms.CharField(label='Key', max_length=100)

class WebhookSubscriptionForm(forms.Form):

    topic = forms.ChoiceField(choices=TOPIC_CHOICES, label='Webhook Topic')
    callback_url = forms.URLField(label='Callback URL')
    format = forms.ChoiceField(choices=[('JSON', 'JSON'), ('XML', 'XML')], label='Format')

class UpdateEventForm(forms.Form):
    
    date = forms.DateField(label='Event Date', widget=forms.TextInput(attrs={'type': 'date'}))
    product_id = forms.CharField(label='Product ID', max_length=100)

class ProductChangeForm(forms.Form):

    product_sku = forms.CharField(label='Product SKU', max_length=100)

    def clean_product_sku(self):
        product_sku = self.cleaned_data['product_sku'].upper()
        if '_' not in product_sku:
            product_sku = f"{product_sku}_S"
        return product_sku
    
class SellingGroupAddForm(forms.Form):

    selling_group_id = forms.CharField(label='Selling Group ID', max_length=100)
    product_variant_id = forms.CharField(label='Products Variant ID', max_length=100)

class DeleteSellingPlanForm(forms.Form):
    selling_plan_group_id = forms.CharField(label='Selling Plan Group ID', max_length=255)
    selling_plan_id = forms.CharField(label='Selling Plan ID', max_length=255)