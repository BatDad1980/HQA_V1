import numpy as np

class TraditionalDecoderNP:
    def __init__(self, fabric, latency_ticks=2):
        self.fabric = fabric
        self.latency_ticks = latency_ticks
        
        self.is_decoding = False
        self.ticks_until_ready = 0
        self.pending_snapshot = None
        
        self.peak_memory_footprint = 0
        self.total_corrections = 0
        
    def step(self):
        # 1. Idle -> Start snapshot
        if not self.is_decoding:
            self.pending_snapshot = self.fabric.get_syndrome_snapshot()
            
            # Memory footprint: massive boolean array
            current_memory = self.pending_snapshot.size
            if current_memory > self.peak_memory_footprint:
                self.peak_memory_footprint = current_memory
                
            self.is_decoding = True
            self.ticks_until_ready = self.latency_ticks
            return
            
        # 2. Countdown latency
        if self.ticks_until_ready > 0:
            self.ticks_until_ready -= 1
            return
            
        # 3. Apply corrections via NumPy mask
        if self.ticks_until_ready == 0 and self.is_decoding:
            self.fabric.apply_corrections_batch(self.pending_snapshot)
            self.total_corrections += np.sum(self.pending_snapshot)
            
            self.is_decoding = False
            self.pending_snapshot = None
