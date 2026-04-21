def compute_slippage(price, quantity, volume):
    impact = (quantity / volume) if volume > 0 else 0
    return price * impact * 0.1


def apply_spread(side, bid, ask):
    return ask if side == "buy" else bid


def enforce_liquidity(quantity, volume, max_rate):
    max_qty = volume * max_rate
    return min(quantity, max_qty)


def execute_order(order, price_row, config):
    side = order["side"]
    base_price = apply_spread(side, price_row["bid"], price_row["ask"])
    qty = enforce_liquidity(
        order["quantity"], price_row["volume"], config["max_participation_rate"]
    )
    slip = compute_slippage(base_price, qty, price_row["volume"])

    final_price = base_price + slip if side == "buy" else base_price - slip
    fee = final_price * qty * (config["fee_bps"] / 10000)

    return {"price": final_price, "quantity": qty, "slippage": slip, "fee": fee}
