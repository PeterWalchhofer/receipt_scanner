import random


def highlight_url(row):
    # different shades of gray for each receipt_url
    random.seed(hash(row["receipt_url"]))  # Ensure consistent color for each URL
    one_to_255 = random.randint(1, 150)
    color = f"rgb({one_to_255}, {one_to_255}, {one_to_255})"

    return [f"background-color: {color}" for _ in row]
