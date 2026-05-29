import time
import torch
from qubit_fabric_cuda import QubitFabricCUDA
from traditional_decoder_cuda import TraditionalDecoderCUDA
from sentinel_reflex_cuda import HQANetworkCUDA

def run_benchmark(ticks=50, width=50, height=50, faults=10, patch_size=5):
    print(f"Initializing Qubit Fabrics ({width}x{height} = {width*height} qubits) on CUDA...")
    
    # Ensure CUDA operations are synchronized before timing
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    
    t0 = time.time()
    fabric_trad = QubitFabricCUDA(width=width, height=height, cascade_threshold=3)
    fabric_trad.inject_hardware_faults(num_faults=faults)
    
    # Exact physical clone onto the GPU
    fabric_hqa = fabric_trad.clone()
    
    decoder = TraditionalDecoderCUDA(fabric_trad, latency_ticks=2)
    hqa = HQANetworkCUDA(fabric_hqa, patch_size=patch_size)
    
    print(f"Running simulation for {ticks} ticks...")
    
    for t in range(ticks):
        # Physics Engine (GPU Tensor Ops)
        fabric_trad.tick()
        fabric_hqa.tick()
        
        # Control Systems
        decoder.step()
        hqa.step()
        
    if torch.cuda.is_available():
        torch.cuda.synchronize()
        
    t1 = time.time()
    elapsed = t1 - t0
    
    # Analyze Results
    trad_errors = fabric_trad.get_error_count()
    hqa_errors = fabric_hqa.get_error_count()
    
    print(f"\n--- RESULTS ---")
    print(f"Time Elapsed: {elapsed:.3f} seconds")
    print(f"Traditional Errors Remaining: {trad_errors}")
    print(f"HQA Errors Remaining: {hqa_errors}")
    print(f"HQA Down-regulated Faults: {hqa.get_down_regulated_count()}")

if __name__ == "__main__":
    if not torch.cuda.is_available():
        print("WARNING: CUDA is not available. Falling back to CPU tensors (still faster than base Python, but not GPU speed).")

    scales = [
        (3162, 3162, 50000, "10 MILLION Qubits"),
        (10000, 10000, 500000, "100 MILLION Qubits (The Compute Horizon)"),
        (31622, 31622, 5000000, "1 BILLION Qubits (The God Protocol)")
    ]
    
    for w, h, f, name in scales:
        print(f"\n======================================")
        print(f"  CUDA ACCELERATED SCALE: {name}")
        print(f"======================================")
        run_benchmark(ticks=50, width=w, height=h, faults=f, patch_size=5)
