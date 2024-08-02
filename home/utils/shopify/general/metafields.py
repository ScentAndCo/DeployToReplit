import json
import shopify

def format_metafield_id(metafield_id):
    if type(metafield_id) != str or metafield_id.isdigit():
        metafield_id = str(metafield_id)
        return f"gid://shopify/Metafield/{metafield_id}"
    return metafield_id

def parse_metafield_data(customer_data):
    metafields = customer_data.get('metafields', {}).get('edges', [])
    metafield_dict = {}

    for edge in metafields:
        node = edge.get('node', {})
        metafield_id = node.get('id')
        if metafield_id:
            metafield_dict[metafield_id] = {
                "id":metafield_id,
                "namespace": node.get("namespace"),
                "key": node.get("key"),
                "value": node.get("value"),
                "type": node.get("type")
            }

    return metafield_dict

def find_metafield_by_namespace_and_key(metafields, namespace, key):
    for _, metafield_data in metafields.items():
        if metafield_data.get('namespace') == namespace and metafield_data.get('key') == key:
            return metafield_data
    return None