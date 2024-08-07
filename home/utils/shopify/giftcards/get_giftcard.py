import json
import shopify


def fetch_all_active_gift_cards():

    shop = "247c21-78.myshopify.com"
    session = shopify.Session(shop, "unstable",
                              "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"
                              )  #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
    shopify.ShopifyResource.activate_session(session)

    def fetch_gift_cards(query, variables):
        response = shopify.GraphQL().execute(query, variables)
        return json.loads(response)

    query = """
    query($after: String) {
        giftCards(first: 100, after: $after, query: "status:ACTIVE") {
            edges {
                node {
                    id
                }
                cursor
            }
            pageInfo {
                hasNextPage
                endCursor
            }
        }
    }
    """

    all_gift_cards = []
    variables = {"after": None}

    while True:
        response_data = fetch_gift_cards(query, variables)
        print("response_data: ", response_data, "\n")
        gift_cards = response_data['data']['giftCards']['edges']
        all_gift_cards.extend(gift_cards)
        page_info = response_data['data']['giftCards']['pageInfo']

        if page_info['hasNextPage']:
            variables['after'] = page_info['endCursor']
        else:
            break

    return all_gift_cards
