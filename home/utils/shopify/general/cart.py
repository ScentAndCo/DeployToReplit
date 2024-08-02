def format_cart_id(cart_id:str):
    if type(cart_id) != str or cart_id.find("gid://shopify/Cart/") == -1:
        cart_id = str(cart_id)
        return f"gid://shopify/Cart/{cart_id}"
    return cart_id