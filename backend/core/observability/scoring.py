import numpy as np


def brier_score(prediction: float, outcome: int) -> float:
    return (prediction - outcome) ** 2


def log_loss(prediction: float, outcome: int) -> float:
    epsilon = 1e-15
    p = np.clip(prediction, epsilon, 1 - epsilon)
    return float(-(outcome * np.log(p) + (1 - outcome) * np.log(1 - p)))
