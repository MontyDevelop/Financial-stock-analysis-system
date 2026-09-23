import json
import time
import urllib.error
import urllib.request

API_BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


# ----------------------- Part 1: Building the Courier (urllib) -----------------------

def fetch_stock_data(stock_name: str) -> dict:
    """Fetches 1 month of daily stock market data via native HTTP GET request."""
    clean_stock_name = stock_name.strip().upper()
    target_url = f"{API_BASE_URL}{clean_stock_name}?range=1mo&interval=1d"

    req = urllib.request.Request(
        target_url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=5.0) as response:
            if response.status != 200:
                return {
                    "success": False,
                    "error": f"Server returned error code {response.status}",
                }

            raw_bytes = response.read()
            raw_text = raw_bytes.decode("utf-8")
            data = json.loads(raw_text)

            return parse_market_payload(clean_stock_name, data)

    except urllib.error.HTTPError as http_err:
        return {
            "success": False,
            "error": f"HTTP {http_err.code}: Ticker not found or API rejected",
        }
    except urllib.error.URLError:
        return {
            "success": False,
            "error": "Network connectivity error: Please check your internet connection",
        }
    except TimeoutError:
        return {"success": False, "error": "Server took too long to answer (> 5.0 seconds)."}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}


# ----------------------- Part 2: The Inspector & Data Cleansing -----------------------

def parse_market_payload(symbol: str, raw_json: dict) -> dict:
    """Traverses raw JSON payload, cleanses holiday nulls, and formats arrays."""
    try:
        chart_data = raw_json.get("chart", {})
        result = chart_data.get("result")

        # Boundary check: Does the ticker symbol actually exist?
        if not result or len(result) == 0:
            return {
                "success": False,
                "error": f"Symbol '{symbol}' does not exist or has no trading history.",
            }

        meta = result[0].get("meta", {})
        indicators = result[0].get("indicators", {})
        quote = indicators.get("quote", [{}])[0]

        raw_timestamps = result[0].get("timestamp", [])
        raw_close_prices = quote.get("close", [])

        # Data Cleansing: Filter out None/null values caused by market holidays
        cleaned_timestamps = []
        cleaned_prices = []

        for ts, price in zip(raw_timestamps, raw_close_prices):
            if price is not None and isinstance(price, (int, float)):
                cleaned_timestamps.append(ts)
                cleaned_prices.append(round(float(price), 2))

        # Verification: Check boundary condition for mathematical algorithms (RSI requires 14)
        if len(cleaned_prices) < 14:
            return {
                "success": False,
                "error": (
                    f"Insufficient trading days available for {symbol}. "
                    f"Minimum 14 required, found {len(cleaned_prices)}."
                ),
            }

        return {
            "success": True,
            "symbol": symbol,
            "currency": meta.get("currency", "USD"),
            "current_price": cleaned_prices[-1],
            "timestamps": cleaned_timestamps,
            "close_prices": cleaned_prices,
            "data_points_count": len(cleaned_prices),
        }

    except KeyError as key_err:
        return {
            "success": False,
            "error": f"Malformed API structure: Missing expected field {str(key_err)}",
        }
    except Exception as err:
        return {"success": False, "error": f"Data parsing exception: {str(err)}"}


# ----------------------- Part 3: Live Stopwatch Smoke Test -----------------------

if __name__ == "__main__":

    # Test Case 1: Valid Active Stock Symbol (Normal Test)
    target_ticker = "AAPL"
    start_time = time.perf_counter()
    result_valid = fetch_stock_data(target_ticker)
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    print(f"\n[Test 1] Valid Symbol Test: '{target_ticker}'")
    print(f" -> Latency: {elapsed_ms:.2f} ms (Target Success Criteria SC2: < 500 ms)")
    print(f" -> Status : {'SUCCESS' if result_valid['success'] else 'FAILED'}")

    if result_valid["success"]:
        print(f" -> Current Price : ${result_valid['current_price']} {result_valid['currency']}")
        print(f" -> Cleaned Points: {result_valid['data_points_count']} trading days extracted")
        print(f" -> Sample Prices : {result_valid['close_prices'][-5:]}")

    # Test Case 2: Erroneous / Invalid Stock Symbol
    invalid_ticker = "INVALID_TICKER_999"
    result_invalid = fetch_stock_data(invalid_ticker)
    print(f"\n[Test 2] Erroneous Symbol Test: '{invalid_ticker}'")
    print(f" -> Handled Gracefully: {not result_invalid['success']}")
    print(f" -> Error Message     : {result_invalid.get('error')}")

    print("\nALL DATA PARSER TESTS EXECUTED!")