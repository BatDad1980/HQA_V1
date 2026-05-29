import numpy as np

class QubitFabricNP:
    def __init__(self, width=2000, height=2000, noise_rate=0.02, cascade_threshold=3):
        self.width = width
        self.height = height
        self.noise_rate = noise_rate
        self.cascade_threshold = cascade_threshold
        
        # Grid: -1 (Isolated), 0 (Healthy), >0 (Error Age)
        # Using int8 to save memory on massive fabrics
        self.grid = np.zeros((height, width), dtype=np.int8)
        
        # Boolean mask for hardware faults
        self.faults = np.zeros((height, width), dtype=bool)

    def inject_hardware_faults(self, num_faults=5000):
        """Randomly assigns physical degradation."""
        # Flat indexing for quick random choice
        indices = np.random.choice(self.width * self.height, size=num_faults, replace=False)
        flat_faults = self.faults.ravel()
        flat_faults[indices] = True
        
        # Immediately set faults to error state
        flat_grid = self.grid.ravel()
        flat_grid[indices] = 1

    def tick(self):
        """Vectorized physics engine tick."""
        # 1. Identify current states
        isolated = (self.grid == -1)
        healthy = (self.grid == 0)
        infected = (self.grid > 0)
        
        # 2. Age existing errors
        self.grid[infected] += 1
        
        # 3. Spontaneous noise and hardware faults
        # Mask where healthy AND (random noise OR is fault)
        noise_mask = np.random.rand(self.height, self.width) < self.noise_rate
        new_errors = healthy & (noise_mask | self.faults)
        self.grid[new_errors] = 1
        
        # 4. Cascade Logic
        # Find cells that hit the cascade threshold
        cascade_sources = (self.grid >= self.cascade_threshold) & ~isolated
        
        if np.any(cascade_sources):
            # Fast vectorized neighborhood expansion (Up, Down, Left, Right)
            infectious_neighbors = np.zeros_like(cascade_sources)
            
            # Shift operations
            infectious_neighbors[:-1, :] |= cascade_sources[1:, :]  # Up
            infectious_neighbors[1:, :] |= cascade_sources[:-1, :]  # Down
            infectious_neighbors[:, :-1] |= cascade_sources[:, 1:]  # Left
            infectious_neighbors[:, 1:] |= cascade_sources[:, :-1]  # Right
            
            # Infect only healthy cells
            new_infections = infectious_neighbors & healthy & ~new_errors
            self.grid[new_infections] = 1

    def apply_corrections_batch(self, mask):
        """Vectorized quenching. mask is boolean array of same shape."""
        # Quench where mask is True and node is not isolated
        to_quench = mask & (self.grid != -1)
        self.grid[to_quench] = 0

    def isolate_nodes_batch(self, mask):
        """Vectorized plastic remapping."""
        self.grid[mask] = -1

    def get_syndrome_snapshot(self):
        """Returns boolean mask of active errors for the global decoder."""
        return self.grid > 0
        
    def get_error_count(self):
        return np.sum(self.grid > 0)
