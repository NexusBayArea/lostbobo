import numpy as np

def compute_residuals(predictions, ground_truths):
    return [abs(p - y) for p, y in zip(predictions, ground_truths)]

def conformal_quantile(residuals, alpha=0.05):
    return float(np.quantile(residuals, 1 - alpha))

def conformal_interval(prediction, residual_quantile):
    return {
        "lower": prediction - residual_quantile,
        "upper": prediction + residual_quantile
    }

def conformal_predict(prediction, calibration_residuals):
    q95 = float(np.quantile(calibration_residuals, 0.95))
    q90 = float(np.quantile(calibration_residuals, 0.90))

    return {
        "prediction": prediction,
        "interval_90": [prediction - q90, prediction + q90],
        "interval_95": [prediction - q95, prediction + q95]
    }
