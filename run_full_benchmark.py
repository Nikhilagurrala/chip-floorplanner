import subprocess
import os
import time
from dotenv import load_dotenv

load_dotenv()

# Official Evaluation Models
MODELS = [
    "Qwen/Qwen2.5-72B-Instruct",
    "meta-llama/Llama-3.1-70B-Instruct",
    "nvidia/Llama-3.1-Nemotron-70B-Instruct-HF"
]

ENV_WS_URL = os.getenv("ENV_WS_URL", "ws://127.0.0.1:7860/ws")
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("API_KEY")

def run_model_benchmark(model_name):
    print(f"\n[START] Starting benchmark for model: {model_name}", flush=True)
    
    test_env = os.environ.copy()
    test_env["MODEL_NAME"] = model_name
    test_env["ENV_WS_URL"] = ENV_WS_URL
    test_env["API_KEY"] = HF_TOKEN
    test_env["HF_TOKEN"] = HF_TOKEN
    
    try:
        # Run inference.py for all tasks
        process = subprocess.Popen(
            ["python", "inference.py"],
            env=test_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Stream output in real-time
        full_stdout = []
        for line in process.stdout:
            print(line, end="", flush=True)
            full_stdout.append(line)
        
        process.wait()
        
        # Log results to file
        with open("benchmark_raw_logs.txt", "a") as f:
            f.write(f"\n--- MODEL: {model_name} ---\n")
            f.write("".join(full_stdout))
            f.write("="*60 + "\n")
            
    except Exception as e:
        print(f"[ERROR] during benchmark for {model_name}: {e}")

if __name__ == "__main__":
    if not HF_TOKEN:
        print("[ERROR] HF_TOKEN environment variable is not set and not found in .env.")
        exit(1)
        
    # Reset log file
    with open("benchmark_raw_logs.txt", "w") as f:
        f.write("=== ULTIMATE CHIP FLOORPLANNER BENCHMARK REPORT ===\n")
    
    for model in MODELS:
        run_model_benchmark(model)
        # Buffer to prevent rate limits
        print("\n[WAIT] Cooldown period (30s)...")
        time.sleep(30)

    print("\n[DONE] ALL BENCHMARKS COMPLETE. See benchmark_raw_logs.txt for details.")
