import numpy as np

class SobolAnalyzer:
    """
    Enterprise-grade Sensitivity Analysis using Variance-based (Sobol) Indices.
    Requires N * (D + 2) simulation runs where D is the number of parameters.
    
    Uses Saltelli sampling with proper A/B/C matrices for Sobol indices.
    Supports seeded RNG for reproducibility.
    """
    
    def __init__(self, problem_dims: int, names: list, seed: int = None):
        self.D = problem_dims
        self.names = names
        self.seed = seed
        if seed is not None:
            self.rng = np.random.RandomState(seed)
        else:
            self.rng = np.random

    def generate_saltelli_samples(self, N: int, bounds: list):
        """
        Generates the Saltelli sample matrix for Sobol sensitivity analysis.
        N: Base number of samples (e.g., 128, 256, 512)
        bounds: List of [min, max] for each parameter
        
        Returns matrix with N * (D + 2) rows:
        - First N rows: Matrix A (independent random samples)
        - Next N rows: Matrix B (independent random samples)
        - Following D*N rows: Cross-matrices Ci (A with column i replaced by B)
        
        These specific matrices are required for computing:
        - S1 (Main Effect): Uses A and Ci
        - ST (Total Effect): Uses A, B, and Ci
        """
        # Create two independent matrices (A and B) using seeded RNG
        A = self.rng.rand(N, self.D)
        B = self.rng.rand(N, self.D)
        
        # Scale to bounds
        for i in range(self.D):
            low, high = bounds[i]
            A[:, i] = A[:, i] * (high - low) + low
            B[:, i] = B[:, i] * (high - low) + low

        # Create the cross-matrices (Ci) for Total Effect calculation
        # Ci = A with column i replaced by B column i
        # This is critical for Sobol ST index calculation
        samples = [A, B]
        for i in range(self.D):
            Ci = np.copy(A)
            Ci[:, i] = B[:, i]
            samples.append(Ci)
            
        return np.vstack(samples)

    def calculate_indices(self, Y: np.ndarray):
        """
        Calculates S1 (Main) and ST (Total) indices from model outputs Y.
        
        Y must be organized as:
        - First N values: Results from matrix A
        - Next N values: Results from matrix B  
        - Following D*N values: Results from cross-matrices C0, C1, ..., C(D-1)
        
        Returns:
        - main_effect (S1): First-order index (individual parameter contribution)
        - total_effect (ST): Total-order index (includes interactions)
        - interaction_strength: ST - S1 (pure interaction effect)
        """
        N = len(Y) // (self.D + 2)
        
        if N == 0:
            return {name: {"main_effect": 0, "total_effect": 0, "interaction_strength": 0} for name in self.names}
        
        A_res = Y[:N]
        B_res = Y[N:2*N]
        
        # Reshape the cross-matrix results
        C_res = Y[2*N:].reshape(self.D, N)

        var_y = np.var(A_res)
        if var_y == 0:
            var_y = 1e-10 # Prevent divide by zero
        
        results = {}
        for i in range(self.D):
            # First-order index (S1) - Main Effect
            # Measures direct contribution of parameter i
            S1 = np.mean(B_res * (C_res[i] - A_res)) / var_y
            
            # Total-order index (ST) - Total Effect
            # Measures total contribution including interactions
            ST = np.mean((A_res - C_res[i])**2) / (2 * var_y)
            
            # Clip results to physical bounds [0, 1]
            main_effect = float(np.clip(S1, 0, 1))
            total_effect = float(np.clip(ST, 0, 1))
            
            # Interaction = ST - S1 (pure interaction effect)
            interaction = max(0.0, total_effect - main_effect)
            
            results[self.names[i]] = {
                "main_effect": main_effect,
                "total_effect": total_effect,
                "interaction_strength": float(np.clip(interaction, 0, 1))
            }
            
        return results
