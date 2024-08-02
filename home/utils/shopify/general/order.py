def format_order_id(order_id):
    if type(order_id) != str or order_id.isdigit():
        order_id = str(order_id)
        order_id = f"gid://shopify/Order/{order_id}"
    return order_id

def format_calculated_order_id(order_id):
    if type(order_id) != str or order_id.isdigit():
        order_id = str(order_id)
        order_id = f"gid://shopify/CalculatedOrder/{order_id}"
    return order_id

def get_order_details(order_data):

    try:
        order_id = order_data.get('id')
        customer_id = order_data.get('customer', {}).get('id')
        financial_status = order_data.get('financial_status')
        tags = order_data.get('tags', [])

        # print("Order Details:")
        # print(f"Order ID: {order_id}")
        # print(f"Customer ID: {customer_id}")
        # print(f"Financial Status: {financial_status}")
        # print(f"Tags: {tags}")

        return {
            "order_id": order_id,
            "customer_id": customer_id,
            "financial_status": financial_status,
            "tags": tags
        }

    except KeyError as e:
        print(f"Key Error: {e}")
        return {"error": f"Key Error: {e}"}
