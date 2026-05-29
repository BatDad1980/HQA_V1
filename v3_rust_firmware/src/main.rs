use rand::{Rng, RngExt};
use std::time::Instant;

#[derive(Clone)]
struct QubitFabric {
    width: usize,
    height: usize,
    noise_rate: f32,
    cascade_threshold: i8,
    grid: Vec<i8>,      // -1: isolated, 0: healthy, >0: infected age
    faults: Vec<bool>,  // true if hardware fault
}

impl QubitFabric {
    fn new(width: usize, height: usize, noise_rate: f32, cascade_threshold: i8) -> Self {
        let size = width * height;
        Self {
            width,
            height,
            noise_rate,
            cascade_threshold,
            grid: vec![0; size],
            faults: vec![false; size],
        }
    }

    fn inject_hardware_faults(&mut self, num_faults: usize) {
        let mut rng = rand::rng();
        let size = self.width * self.height;
        let mut injected = 0;
        while injected < num_faults {
            let idx = rng.random_range(0..size);
            if !self.faults[idx] {
                self.faults[idx] = true;
                self.grid[idx] = 1;
                injected += 1;
            }
        }
    }

    fn tick(&mut self) {
        let size = self.width * self.height;
        let mut next_grid = self.grid.clone();
        let mut rng = rand::rng();

        for i in 0..size {
            // 1. Skip isolated
            if self.grid[i] == -1 {
                continue;
            }

            // 2. Age existing errors
            if self.grid[i] > 0 {
                next_grid[i] += 1;
            } 
            // 3. Spontaneous noise & faults
            else if self.grid[i] == 0 {
                if self.faults[i] || rng.random::<f32>() < self.noise_rate {
                    next_grid[i] = 1;
                }
            }
            
            // 4. Cascade Logic
            if next_grid[i] >= self.cascade_threshold {
                let x = i % self.width;
                let y = i / self.width;

                let neighbors = [
                    (x as isize - 1, y as isize),
                    (x as isize + 1, y as isize),
                    (x as isize, y as isize - 1),
                    (x as isize, y as isize + 1),
                ];

                for &(nx, ny) in &neighbors {
                    if nx >= 0 && nx < self.width as isize && ny >= 0 && ny < self.height as isize {
                        let n_idx = (ny as usize) * self.width + (nx as usize);
                        if self.grid[n_idx] == 0 {
                            next_grid[n_idx] = 1; // Infect healthy neighbor
                        }
                    }
                }
            }
        }
        self.grid = next_grid;
    }

    fn get_error_count(&self) -> usize {
        self.grid.iter().filter(|&&v| v > 0).count()
    }
}

struct TraditionalDecoder {
    latency_ticks: usize,
    is_decoding: bool,
    ticks_until_ready: usize,
    pending_snapshot: Option<Vec<bool>>,
    peak_memory_footprint: usize,
    total_corrections: usize,
}

impl TraditionalDecoder {
    fn new(latency_ticks: usize) -> Self {
        Self {
            latency_ticks,
            is_decoding: false,
            ticks_until_ready: 0,
            pending_snapshot: None,
            peak_memory_footprint: 0,
            total_corrections: 0,
        }
    }

    fn step(&mut self, fabric: &mut QubitFabric) {
        if !self.is_decoding {
            let snapshot: Vec<bool> = fabric.grid.iter().map(|&v| v > 0).collect();
            let mem = snapshot.len();
            if mem > self.peak_memory_footprint {
                self.peak_memory_footprint = mem;
            }
            self.pending_snapshot = Some(snapshot);
            self.is_decoding = true;
            self.ticks_until_ready = self.latency_ticks;
            return;
        }

        if self.ticks_until_ready > 0 {
            self.ticks_until_ready -= 1;
            return;
        }

        if self.ticks_until_ready == 0 && self.is_decoding {
            if let Some(snap) = &self.pending_snapshot {
                for (i, &has_error) in snap.iter().enumerate() {
                    if has_error && fabric.grid[i] != -1 {
                        fabric.grid[i] = 0;
                        self.total_corrections += 1;
                    }
                }
            }
            self.is_decoding = false;
            self.pending_snapshot = None;
        }
    }
}

struct HQANetwork {
    patch_size: usize,
    plasticity_threshold: i16,
    fault_counters: Vec<i16>,
    total_corrections: usize,
    peak_memory_footprint: usize,
}

impl HQANetwork {
    fn new(size: usize, patch_size: usize, plasticity_threshold: i16) -> Self {
        Self {
            patch_size,
            plasticity_threshold,
            fault_counters: vec![0; size],
            total_corrections: 0,
            peak_memory_footprint: patch_size * patch_size,
        }
    }

    fn step(&mut self, fabric: &mut QubitFabric) {
        for i in 0..fabric.grid.len() {
            if fabric.grid[i] > 0 {
                self.fault_counters[i] += 1;
                
                if self.fault_counters[i] >= self.plasticity_threshold {
                    fabric.grid[i] = -1; // Isolate
                } else {
                    fabric.grid[i] = 0;  // Quench
                    self.total_corrections += 1;
                }
            }
        }
    }

    fn down_regulated_count(&self) -> usize {
        self.fault_counters.iter().filter(|&&c| c >= self.plasticity_threshold).count()
    }
}

fn run_benchmark(ticks: usize, width: usize, height: usize, faults: usize, patch_size: usize, name: &str) {
    println!("\n======================================");
    println!("  RUST BARE-METAL SCALE: {}", name);
    println!("======================================");
    println!("Initializing Qubit Fabrics ({}x{} = {} qubits)...", width, height, width * height);

    let start = Instant::now();

    let mut fabric_trad = QubitFabric::new(width, height, 0.02, 3);
    fabric_trad.inject_hardware_faults(faults);
    let mut fabric_hqa = fabric_trad.clone();

    let mut decoder = TraditionalDecoder::new(2);
    let mut hqa = HQANetwork::new(width * height, patch_size, 5);

    println!("Running simulation for {} ticks...", ticks);

    for _ in 0..ticks {
        fabric_trad.tick();
        fabric_hqa.tick();

        decoder.step(&mut fabric_trad);
        hqa.step(&mut fabric_hqa);
    }

    let duration = start.elapsed();

    println!("\n--- RESULTS ---");
    println!("Time Elapsed: {:?}", duration);
    println!("Traditional Errors Remaining: {}", fabric_trad.get_error_count());
    println!("HQA Errors Remaining: {}", fabric_hqa.get_error_count());
    println!("HQA Down-regulated Faults: {}", hqa.down_regulated_count());
}

fn main() {
    let scales = vec![
        (31622, 31622, 5000000, "1 BILLION Qubits (The God Protocol)")
    ];

    for (w, h, f, name) in scales {
        run_benchmark(50, w, h, f, 5, name);
    }
}
