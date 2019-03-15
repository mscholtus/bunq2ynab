import bunq


def get_user_id(user_name):
    for u in bunq.get('v1/user'):
        for k, v in u.items():
            if (v["display_name"].casefold() == user_name.casefold() or
                    str(v["id"]) == user_name):
                return str(v["id"])
    raise Exception("BUNQ user '{0}' not found".format(user_name))

def get_account_type(user_id, account_name):
    reply = bunq.get('v1/user/' + user_id + '/monetary-account/' + account_name)
    return next(iter(reply[0].keys()))

def get_account_id(user_id, account_name):
    account_type = get_account_type(user_id, account_name)
    reply = bunq.get('v1/user/' + user_id + '/' + bunq.get_account_path(account_type))
    for a in [a[account_type] for a in reply]:
        if (a["description"].casefold() == account_name.casefold() or
                str(a["id"]) == account_name):
            return str(a["id"])
    raise Exception("BUNQ account '{0}' not found".format(account_name))


def get_callbacks(user_id, account_id):
    account_type = get_account_type(user_id, account_id)
    method = 'v1/user/{0}/monetary-account/{1}'.format(user_id, account_id)
    result = bunq.get(method)
    return result[0][account_type]["notification_filters"]


def put_callbacks(user_id, account_id, new_notifications):
    account_type = get_account_type(user_id, account_id)
    data = {
         "notification_filters": new_notifications
    }
    method = 'v1/user/{0}/' + bunq.get_account_path(account_type) + '/{1}'.format(
                                                           user_id, account_id)
    bunq.put(method, data)


def get_transactions(user_id, account_id):
    method = ("v1/user/{0}/monetary-account/{1}/payment?count=100"
              .format(user_id, account_id))
    payments = bunq.get(method)

    print("Translating payments...")
    transactions = []
    first_day = None
    unsorted_payments = [p["Payment"] for p in payments]
    payments = sorted(unsorted_payments, key=lambda p: p["created"])
    for p in payments:
        if p["amount"]["currency"] != "EUR":
            raise Exception("Non-euro payment: " + p["amount"]["currency"])
        date = p["created"][:10]
        if not first_day or date < first_day:
            first_day = date

        transactions.append({
            "amount": p["amount"]["value"],
            "date": date,
            "payee": p["counterparty_alias"]["display_name"],
            "description": p["description"]
        })

    # For correct duplicate calculation, return only complete days
    return [t for t in transactions if first_day < t["date"]]
