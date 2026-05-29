import torch

class QubitFabricCUDA:
    def __init__(self, width=2000, height=2000, noise_rate=0.02, cascade_threshold=3):
        self.width = width
        self.height = height
        self.noise_rate = noise_rate
        self.cascade_threshold = cascade_threshold
        
        # Grid: -1 (Isolated), 0 (Healthy), >0 (Error Age)
        # Allocate directly on the GPU
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.grid = torch.zeros((height, width), dtype=torch.int8, device=self.device)
        self.faults = torch.zeros((height, width), dtype=torch.bool, device=self.device)

    def inject_hardware_faults(self, num_faults=5000):
        # Flatten the faults tensor to use random permutation indices
        indices = torch.randperm(self.width * self.height, device=self.device)[:num_faults]
        flat_faults = self.faults.view(-1)
        flat_faults[indices] = True
        
        flat_grid = self.grid.view(-1)
        flat_grid[indices] = 1

    def tick(self):
        # 1. Identify current states directly on GPU
        isolated = (self.grid == -1)
        healthy = (self.grid == 0)
        infected = (self.grid > 0)
        
        # 2. Age existing errors
        self.grid[infected] += 1
        
        # 3. Spontaneous noise and hardware faults
        noise_mask = torch.rand((self.height, self.width), device=self.device) < self.noise_rate
        new_errors = healthy & (noise_mask | self.faults)
        self.grid[new_errors] = 1
        
        # 4. Cascade Logic
        cascade_sources = (self.grid >= self.cascade_threshold) & ~isolated
        
        if cascade_sources.any():
            infectious_neighbors = torch.zeros_like(cascade_sources, device=self.device)
            
            # Fast vectorized neighborhood expansion on GPU
            infectious_neighbors[:-1, :] |= cascade_sources[1:, :]  # Up
            infectious_neighbors[1:, :] |= cascade_sources[:-1, :]  # Down
            infectious_neighbors[:, :-1] |= cascade_sources[:, 1:]  # Left
            infectious_neighbors[:, 1:] |= cascade_sources[:, :-1]  # Right
            
            new_infections = infectious_neighbors & healthy & ~new_errors
            self.grid[new_infections] = 1

    def apply_corrections_batch(self, mask):
        to_quench = mask & (self.grid != -1)
        self.grid[to_quench] = 0

    def isolate_nodes_batch(self, mask):
        self.grid[mask] = -1

    def get_syndrome_snapshot(self):
        return self.grid > 0
        
    def get_error_count(self):
        return (self.grid > 0).sum().item()

    def clone(self):
        # Deep clone logic for the CUDA object
        new_fabric = QubitFabricCUDA(self.width, self.height, self.noise_rate, self.cascade_threshold)
        new_fabric.grid = self.grid.clone()
        new_fabric.faults = self.faults.clone()
        return new_fabric
