class TraditionalDecoder:
    def __init__(self, fabric, latency_ticks=2):
        self.fabric = fabric
        self.latency_ticks = latency_ticks
        
        self.is_decoding = False
        self.ticks_until_ready = 0
        self.pending_snapshot = None
        
        # Metrics
        self.peak_memory_footprint = 0
        self.total_corrections = 0
        
    def step(self):
        """Simulates the decoding lifecycle."""
        # 1. If idle, take a global snapshot
        if not self.is_decoding:
            self.pending_snapshot = self.fabric.get_syndrome_snapshot()
            
            # Memory footprint: requires loading the entire O(N^2) grid into memory for matrix operations
            current_memory = self.fabric.width * self.fabric.height
            if current_memory > self.peak_memory_footprint:
                self.peak_memory_footprint = current_memory
                
            self.is_decoding = True
            self.ticks_until_ready = self.latency_ticks
            return
            
        # 2. If decoding, countdown latency
        if self.ticks_until_ready > 0:
            self.ticks_until_ready -= 1
            return
            
        # 3. Apply corrections based on the OLD snapshot
        if self.ticks_until_ready == 0 and self.is_decoding:
            for y in range(self.fabric.height):
                for x in range(self.fabric.width):
                    if self.pending_snapshot[y][x] == 1:
                        self.fabric.apply_correction(x, y)
                        self.total_corrections += 1
            
            # Reset
            self.is_decoding = False
            self.pending_snapshot = None
