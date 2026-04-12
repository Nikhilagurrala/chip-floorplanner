import os
import getpass

print("\u2550" * 40)
print("  Chip Floorplanner - Secure Key Setup")
print("\u2550" * 40)

# getpass hides the input while you type/paste
token = getpass.getpass("\n1. Please paste your Hugging Face Token (it will be hidden): ").strip()

if not token.startswith("hf_"):
    print("\n[WARNING] That doesn't look like a standard HF token.")

with open(".env", "w") as f:
    f.write(f"HF_TOKEN={token}\n")
    f.write("ENV_WS_URL=ws://127.0.0.1:7861/ws\n")
    f.write("BENCHMARK_LEVELS=easy,medium\n")
    f.write("REPETITIONS=1\n")

print("\n\u2705 Done! Created .env file safely.")
print("You can now run the benchmark by saying 'Run the benchmark'.\n")
