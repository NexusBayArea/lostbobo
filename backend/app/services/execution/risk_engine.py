import numpy as np


def compute_drawdown(equity, peak):
    peak = max(peak, equity)
    dd = (equity - peak) / peak if peak > 0 else 0
    return dd, peak


def rolling_vol(returns, window=20):
    if len(returns) < window:
        return 0.0
    return float(np.std(returns[-window:]) * np.sqrt(252))


def compute_var(returns, alpha=0.05):
    if len(returns) == 0:
        return 0.0
    return float(np.percentile(returns, alpha * 100))


def compute_cvar(returns, alpha=0.05):
    var = compute_var(returns, alpha)
    tail = [r for r in returns if r <= var]
    return float(np.mean(tail)) if tail else var


def evaluate_risk(state, returns, config):
    events = []

    # Drawdown
    dd, peak = compute_drawdown(state["equity"], state["peak"])
    state["drawdown"] = dd
    state["peak"] = peak

    if dd < config.get("max_drawdown", -0.25):
        state["status"] = "halted"
        events.append(("MAX_DRAWDOWN", "CRITICAL"))

    # Volatility
    vol = rolling_vol(returns)
    state["rolling_vol"] = vol

    if vol > config.get("vol_target", 0.15) * 1.5:
        state["status"] = "restricted"
        events.append(("VOL_SPIKE", "HIGH"))

    # VaR
    var = compute_var(returns)
    state["var_95"] = var

    if var < config.get("var_limit", -0.03):
        state["status"] = "restricted"
        events.append(("VAR_BREACH", "HIGH"))

    # CVaR
    cvar = compute_cvar(returns)
    state["cvar_95"] = cvar

    if cvar < config.get("cvar_limit", -0.05):
        state["status"] = "halted"
        events.append(("CVAR_BREACH", "CRITICAL"))

    return state, events


def apply_risk_controls(orders, state):
    if state["status"] == "halted":
        return []

    if state["status"] == "restricted":
        return [{**o, "quantity": o["quantity"] * 0.25} for o in orders]

    return orders
