from pathlib import Path

# Test what the bulk backtest report generator does
project_root = Path(__file__).parent.parent.resolve()
output_dir = project_root / "data" / "reports"
print(f"Project root: {project_root}")
print(f"Output dir: {output_dir}")
print(f"Output dir exists: {output_dir.exists()}")

try:
    output_dir.mkdir(parents=True, exist_ok=True)
    print("✅ mkdir succeeded")
except Exception as e:
    print(f"❌ mkdir failed: {e}")
