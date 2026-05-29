import time
import copy
from qubit_fabric_np import QubitFabricNP
from traditional_decoder_np import TraditionalDecoderNP
from sentinel_reflex_np import HQANetworkNP

def run_benchmark(ticks=50, width=50, height=50, faults=10, patch_size=5):
    print(f"Initializing Qubit Fabrics ({width}x{height} = {width*height} qubits)...")
    
    t0 = time.time()
    fabric_trad = QubitFabricNP(width=width, height=height, cascade_threshold=3)
    fabric_trad.inject_hardware_faults(num_faults=faults)
    
    # Exact physical clone
    fabric_hqa = copy.deepcopy(fabric_trad)
    
    decoder = TraditionalDecoderNP(fabric_trad, latency_ticks=2)
    hqa = HQANetworkNP(fabric_hqa, patch_size=patch_size)
    
    print(f"Running simulation for {ticks} ticks...")
    
    for t in range(ticks):
        # Physics Engine
        fabric_trad.tick()
        fabric_hqa.tick()
        
        # Control Systems
        decoder.step()
        hqa.step()
        
    t1 = time.time()
    elapsed = t1 - t0
    
    # Analyze Results
    trad_errors = fabric_trad.get_error_count()
    hqa_errors = fabric_hqa.get_error_count()
    
    trad_mem = decoder.peak_memory_footprint
    hqa_mem = hqa.peak_memory_footprint
    
    print(f"\n--- RESULTS ---")
    print(f"Time Elapsed: {elapsed:.3f} seconds")
    print(f"Traditional Errors Remaining: {trad_errors}")
    print(f"HQA Errors Remaining: {hqa_errors}")
    print(f"HQA Down-regulated Faults: {hqa.get_down_regulated_count()}")

if __name__ == "__main__":
    scales = [
        (1000, 1000, 5000, "1 MILLION Qubits"),
        (2000, 2000, 20000, "4 MILLION Qubits")
    ]
    
    for w, h, f, name in scales:
        print(f"\n======================================")
        print(f"  VECTORIZED TESTING SCALE: {name}")
        print(f"======================================")
        run_benchmark(ticks=50, width=w, height=h, faults=f, patch_size=5)
