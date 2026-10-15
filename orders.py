"""Order processing logic."""
import database
import auth

TAX = 0.15

separator = "=============================="


def _calculate_items_total(items):
    total = 0
    for item in items:
        book = database.get_book(item["book_id"])
        if not book:
            print("Book not found")
            continue
        if book[3] < item["qty"]:
            if book[3] > 0:
                print("Only " + str(book[3]) + " units available for " + book[1])
            else:
                print("Book out of stock: " + book[1])
            continue
        if item["qty"] <= 0:
            print("Invalid quantity")
            continue
        total += book[2] * item["qty"]
        database.update_stock(book[0], book[3] - item["qty"])
    return total


def _apply_coupon(total, coupon):
    discounts = {
        "WELCOME10": 0.9,
        "BLACKFRIDAY": 0.5,
        "STAFF": 0.7,
    }
    if coupon in discounts:
        return total * discounts[coupon]
    return total


def _add_shipping(total, shipping):
    shipping_costs = {"express": 10, "standard": 3}
    return total + shipping_costs.get(shipping, 0)


def process_order(token, items, coupon=None, shipping="standard", log=None):
    if log is None:
        log = []

    username = auth.sessions.get(token)
    if username is None:
        print("Invalid session")
        return None
    if items == []:
        print("Empty order")
        return None
    total = _calculate_items_total(items)
    total = _apply_coupon(total, coupon)
    total = _add_shipping(total, shipping)
    total += total * TAX
    order_id = len(log) + 1
    database.save_order(order_id, username, total, "PENDING")
    log.append(order_id)
    return round(total, 2)


def print_invoice(username, items):
    print(separator)
    print("BOOKSTORE INVOICE")
    print("Customer: " + username)
    print(separator)
    subtotal = 0
    for item in items:
        book = database.get_book(item["book_id"])
        line_total = book[2] * item["qty"]
        subtotal = subtotal + line_total
        print(book[1] + " x" + str(item["qty"]) + " = " + str(line_total))
    tax = subtotal * TAX
    print("Subtotal: " + str(round(subtotal, 2)))
    print("Tax: " + str(round(tax, 2)))
    print("Total: " + str(round(subtotal + tax, 2)))
    print(separator)


def print_quote(username, items):
    print(separator)
    print("BOOKSTORE QUOTE")
    print("Customer: " + username)
    print(separator)
    subtotal = 0
    for item in items:
        book = database.get_book(item["book_id"])
        line_total = book[2] * item["qty"]
        subtotal = subtotal + line_total
        print(book[1] + " x" + str(item["qty"]) + " = " + str(line_total))
    tax = subtotal * TAX
    print("Subtotal: " + str(round(subtotal, 2)))
    print("Tax: " + str(round(tax, 2)))
    print("Total: " + str(round(subtotal + tax, 2)))
    print("This quote is valid for 7 days.")
    print(separator)


def cancel_order(order_id):
    try:
        conn = database.get_connection()
        conn.execute(f"UPDATE orders SET status = 'CANCELLED' WHERE id = {order_id}")
        conn.commit()
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error cancelling order {order_id}: {e}")
