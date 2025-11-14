import requests
from bs4 import BeautifulSoup
import json
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

HEADERS = {"User-Agent": "Mozilla/5.0"}

def extract_price(url):
    page = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(page.text, "html.parser")

    # AMAZON
    amz = soup.select_one("#priceblock_ourprice, #priceblock_dealprice")
    if amz:
        return float(amz.text.replace("₹", "").replace(",", "").strip())

    # FLIPKART
    fk = soup.select_one("._30jeq3._16Jk6d")
    if fk:
        return float(fk.text.replace("₹", "").replace(",", "").strip())

    return None


def send_email(message):
    sender = "YOUR_EMAIL@gmail.com"
    password = "YOUR_APP_PASSWORD"
    receiver = "YOUR_EMAIL@gmail.com"

    msg = MIMEText(message)
    msg["Subject"] = "Price Drop Alert"
    msg["From"] = sender
    msg["To"] = receiver

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())


def calculate_stats(history):
    prices = [h["price"] for h in history]

    lowest = min(prices)
    highest = max(prices)
    avg = sum(prices) / len(prices)

    one_year_ago = datetime.now().timestamp() - (365 * 24 * 60 * 60)
    last_year_prices = [h["price"] for h in history if h["date"] >= one_year_ago]

    if last_year_prices:
        year_low = min(last_year_prices)
        year_high = max(last_year_prices)
        year_avg = sum(last_year_prices) / len(last_year_prices)
    else:
        year_low = year_high = year_avg = None

    return lowest, highest, avg, year_low, year_high, year_avg


def main():
    with open("products.json", "r") as f:
        products = json.load(f)

    for item in products:
        url = item["url"]
        old_price = item["last_price"]
        history = item.get("history", [])

        current_price = extract_price(url)
        print(url, " → ", current_price)

        if current_price is None:
            continue

        # Save history
        history.append({
            "price": current_price,
            "date": datetime.now().timestamp()
        })

        # First-time run
        if old_price == 0:
            item["last_price"] = current_price
            item["history"] = history
            continue

        # Stats
        lowest, highest, avg, y_low, y_high, y_avg = calculate_stats(history)

        # Price dropped
        if current_price < old_price:
            drop = old_price - current_price

            msg = f"""
PRICE DROP ALERT 🔥

URL: {url}

Old Price: ₹{old_price}
New Price: ₹{current_price}
Drop Amount: ₹{drop}

📉 Price Statistics:
---------------------
Lowest Price Ever: ₹{lowest}
Highest Price Ever: ₹{highest}
Average Price All-Time: ₹{avg:.2f}

📊 1-Year Price Stats:
---------------------
Lowest (1Y): {y_low}
Highest (1Y): {y_high}
Average (1Y): {y_avg}

📆 Total Price Records: {len(history)}
"""

            send_email(msg)

        # Update last price
        item["last_price"] = current_price
        item["history"] = history

    with open("products.json", "w") as f:
        json.dump(products, f, indent=4)


if __name__ == "__main__":
    main()

