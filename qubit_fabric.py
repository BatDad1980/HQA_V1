import random
import copy

class QubitFabric:
    def __init__(self, width=20, height=20, noise_rate=0.02, cascade_threshold=3):
        self.width = width
        self.height = height
        self.noise_rate = noise_rate
        self.cascade_threshold = cascade_threshold
        
        # 0 = Healthy, >0 = Age of the error (ticks since it appeared)
        self.grid = [[0 for _ in range(width)] for _ in range(height)]
        
        # Track permanently degraded nodes (hardware faults)
        self.faults = set()
        
    def inject_hardware_faults(self, num_faults=5):
        """Simulates physical degradation where certain qubits are always noisy."""
        for _ in range(num_faults):
            x, y = random.randint(0, self.width-1), random.randint(0, self.height-1)
            self.faults.add((x, y))
            self.grid[y][x] = 1

    def tick(self):
        """Advances simulation by one time step."""
        new_grid = copy.deepcopy(self.grid)
        
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == -1:
                    new_grid[y][x] = -1
                # 1. Spontaneous Noise
                elif self.grid[y][x] == 0:
                    if random.random() < self.noise_rate or (x, y) in self.faults:
                        new_grid[y][x] = 1
                else:
                    # 2. Age existing errors
                    new_grid[y][x] += 1
                    
                    # 3. Cascade Logic (Infect neighbors if error is too old)
                    if new_grid[y][x] >= self.cascade_threshold and self.grid[y][x] != -1:
                        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                # Neighbor becomes infected (age 1) if it was healthy
                                if self.grid[ny][nx] == 0:
                                    new_grid[ny][nx] = 1

        self.grid = new_grid

    def apply_correction(self, x, y):
        """External control mechanism to quench an error."""
        if 0 <= x < self.width and 0 <= y < self.height:
            if self.grid[y][x] != -1: # Don't quench isolated nodes
                self.grid[y][x] = 0
                
    def isolate_node(self, x, y):
        """Structurally isolate a degraded node so it cannot cascade."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = -1

    def get_syndrome_snapshot(self):
        """Returns a boolean mask of errors for global decoders."""
        return [[1 if cell > 0 else 0 for cell in row] for row in self.grid]
        
    def get_error_count(self):
        count = 0
        for row in self.grid:
            for cell in row:
                if cell > 0: count += 1
        return count
