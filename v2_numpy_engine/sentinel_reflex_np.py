import numpy as np

class HQANetworkNP:
    def __init__(self, fabric, patch_size=5, plasticity_threshold=5):
        self.fabric = fabric
        self.patch_size = patch_size
        self.plasticity_threshold = plasticity_threshold
        
        # Parallel tracking of fault frequency across all edge nodes
        # In a real hardware deployment, this sits in SRAM on the local patch controller
        self.fault_counters = np.zeros((fabric.height, fabric.width), dtype=np.int16)
        
        self.total_corrections = 0
        self.peak_memory_footprint = patch_size * patch_size  # O(1) bound per core
        
    def step(self):
        """Zero-latency local processing tick, vectorized for simulation speed."""
        
        # 1. Identify where errors exist right now that are NOT isolated
        active_errors = (self.fabric.grid > 0)
        
        # 2. Increment local fault counters where active errors appear
        self.fault_counters[active_errors] += 1
        
        # 3. Plasticity Check: Nodes that have failed repeatedly
        hardware_fault_mask = (self.fault_counters >= self.plasticity_threshold)
        
        # Isolate them structurally
        if np.any(hardware_fault_mask):
            self.fabric.isolate_nodes_batch(hardware_fault_mask)
            
        # 4. Quench the remaining errors (Local Reflex)
        # We only quench active errors that are NOT hardware faults
        quench_mask = active_errors & ~hardware_fault_mask
        
        if np.any(quench_mask):
            self.fabric.apply_corrections_batch(quench_mask)
            self.total_corrections += np.sum(quench_mask)

    def get_down_regulated_count(self):
        return np.sum(self.fault_counters >= self.plasticity_threshold)
