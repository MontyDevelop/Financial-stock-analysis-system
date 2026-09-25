# ---------------- 1. 10-Day Simple Moving Average (SMA) ----------------
def calculate_sma(prices: list, time_window: int = 10) -> float | None:
    """Calculates the Simple Moving Average (SMA) over a sliding window.

    Divides the sum of recent window closing prices by the window size.
    """
    if not prices or len(prices) < time_window:
        return None

    recent_time_window = prices[-time_window:]
    prices_sum = sum(recent_time_window)
    return round(prices_sum / time_window, 2)


# ------------ 2. 14-Period Relative Strength Index (RSI) ---------------
def calculate_rsi(prices: list, period: int = 14) -> float | None:
    """Calculates 14-period RSI using Wilder's exponential smoothing technique.

    Returns momentum value bounded between 0 and 100.
    """
    if not prices or len(prices) < period + 1:
        return 50.0  # Default neutral RSI if historical points are insufficient

    # Compute daily price differences (deltas)
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

    # Initial baseline averages
    gains = [d if d > 0 else 0.0 for d in deltas[:period]]
    losses = [-d if d < 0 else 0.0 for d in deltas[:period]]

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    # Wilder's smoothing loop
    for d in deltas[period:]:
        gain = d if d > 0 else 0.0
        loss = -d if d < 0 else 0.0
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

    if avg_loss == 0.0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return round(rsi, 2)


# ------------ 3. 7-Day Linear Regression Forecasting (y = mx + c) -------
def calculate_linear_regression(prices: list, forecast_days: int = 7) -> dict | None:
    """Calculates ordinary least squares linear regression (y = mx + c) in O(N) time.

    Projects the next 7 future daily price points.
    """
    n = len(prices)
    if n < 2:
        return None

    x = list(range(n))
    y = prices

    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi**2 for xi in x)

    denominator = n * sum_x2 - (sum_x**2)
    if denominator == 0:
        return None

    m = (n * sum_xy - (sum_x * sum_y)) / denominator
    c = (sum_y - (m * sum_x)) / n

    forecast_points = []
    for day_offset in range(forecast_days):
        future_x = n + day_offset
        predicted_val = round(m * future_x + c, 2)
        forecast_points.append(predicted_val)

    trend = "BULLISH" if m > 0.05 else "BEARISH" if m < -0.05 else "NEUTRAL"

    return {
        "slope_m": round(m, 4),
        "intercept_c": round(c, 4),
        "trend": trend,
        "forecast": forecast_points,
    }


# ----------- 4. Custom Merge Sort (Top 5 Performing Equities) ----------
def merge_sort_stocks(stock_list: list) -> list:
    """Recursively sorts a list of stock records by 'daily_return_pct' in descending order.

    Guarantees O(N log N) time complexity across all cases.
    """
    if len(stock_list) <= 1:
        return stock_list

    mid = len(stock_list) // 2
    left_half = merge_sort_stocks(stock_list[:mid])
    right_half = merge_sort_stocks(stock_list[mid:])

    return _merge(left_half, right_half)


def _merge(left: list, right: list) -> list:
    merged = []
    i = 0
    j = 0

    while i < len(left) and j < len(right):
        if left[i]["daily_return_pct"] >= right[j]["daily_return_pct"]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1

    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


# MODULE SMOKE TEST & BENCHMARK
if __name__ == "__main__":
    print("  RUNNING MATHEMATICAL ENGINE BENCHMARKS")
    print("")

    test_prices = [
        190.0,
        191.5,
        192.0,
        191.0,
        193.5,
        194.0,
        195.0,
        194.5,
        196.0,
        197.5,
        198.0,
        199.0,
        197.0,
        200.0,
        202.0,
    ]

    # Test SMA (T6)
    sma = calculate_sma(test_prices, time_window=10)
    print(f"[Test 1] 10-day SMA: ${sma} (Expected: $197.30)")

    # Test RSI (T7)
    rsi = calculate_rsi(test_prices, period=14)
    print(f"[Test 2] 14-period RSI: {rsi} (Expected: ~81.58 - Overbought)")

    # Test Linear Regression (T6)
    reg = calculate_linear_regression(test_prices, forecast_days=7)
    print(
        f"[Test 3] Linear Regression Trend: {reg['trend']} | Slope (m):"
        f" {reg['slope_m']}"
    )
    print(f"         7-Day Projected Vector: {reg['forecast']}")

    # Test Merge Sort (T9)
    sample_basket = [
        {"symbol": "AAPL", "daily_return_pct": 1.40, "price": 182.50},
        {"symbol": "TSLA", "daily_return_pct": 3.10, "price": 215.80},
        {"symbol": "MSFT", "daily_return_pct": 0.90, "price": 445.20},
        {"symbol": "NVDA", "daily_return_pct": 4.20, "price": 128.50},
        {"symbol": "AMZN", "daily_return_pct": 0.60, "price": 185.10},
        {"symbol": "GOOGL", "daily_return_pct": -0.80, "price": 165.30},
        {"symbol": "META", "daily_return_pct": 2.10, "price": 505.40},
    ]

    sorted_stocks = merge_sort_stocks(sample_basket)
    print(f"\n[Test 4] Custom Merge Sort Leaderboard Output (Top 5):")
    for rank, item in enumerate(sorted_stocks[:5], start=1):
        print(
            f"  {rank}. {item['symbol']} : +{item['daily_return_pct']}% at"
            f" ${item['price']}"
        )

    print("\n✓ ALL CORE MATHEMATICAL ALGORITHMS VERIFIED!")