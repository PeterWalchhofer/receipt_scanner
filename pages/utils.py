import random


def highlight_url(row):
    # different shades of gray for each receipt_url
    random.seed(hash(row["receipt_url"]))  # Ensure consistent color for each URL
    one_to_255 = random.randint(1, 150)
    color = f"rgb({one_to_255}, {one_to_255}, {one_to_255})"

    return [f"background-color: {color}" for _ in row]


def get_location(row):
    if row["company_name"] == "Marktwagen":
        return "Marktwagen"
    elif row["company_name"] == "Kemmts Eina":
        return "Kemmts Eina"
    elif row["source"] == "RECHNUNGSAPP":
        return "Lieferungen"
    elif row["source"] == "REGISTRIERKASSA":
        return "Hofladen"
    else:
        return "Other"
