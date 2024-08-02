def format_product_id(product_id):
    if type(product_id) != str or product_id.isdigit():
        product_id = str(product_id)
        return f"gid://shopify/Product/{product_id}"
    return product_id

def format_product_variant_id(product_id):
    if type(product_id) != str or product_id.isdigit():
        product_id = str(product_id)
        return f"gid://shopify/ProductVariant/{product_id}"
    return product_id