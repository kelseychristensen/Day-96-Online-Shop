import stripe

stripe.api_key = 'sk_test_51MgZgULMezHay0pYBXNXx3oxtSZz9onHqOqoKAsL2VIYwWOdnCLd653pgjaNeAWoZRqyWkG7bgEixDGDVUhOCqHg00N5B0df8V'

products = stripe.Product.list(limit=4)["data"]

cart = []

for product in products:
    cart.append(product)
    cart.append(product)

print(cart)

cart_items = []

for item in cart:
    if item.id in cart_items:
        pass
    else:
        cart_items.append({'price': item.default_price,
                           'quantity': cart.count(item.id)})

print(cart_items)