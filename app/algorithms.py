# Part 1

# 14 RSI

# 1000


# 10

# 10 days simple moving average (SMA)

# 1,2,3,4,5,6,7,8,9,10

# add all / 10

# ----------------10 days SMP Calculation--------------

def calculate_smp(prices: list, time_window: int = 10) -> float | None:
    if not prices or len(prices) < time_window:
        return None

    recent_time_window = prices[-time_window:]
    prices_sum = sum(recent_time_window)
    return round((prices_sum / recent_time_window),2)

# -------------14 days RSI (Realtive strength index) --------------------


def calculate_rsi(prices: list, period: int = 14) -> float | None:
    if not prices or len(prices) < period + 1:
            return None

    # computing daily prices differences (deltas)
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
         
    