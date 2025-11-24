
import sys
import os
import logging

# Add project root to path
sys.path.append(os.getcwd())

# Configure logging
logging.basicConfig(level=logging.INFO)

from aperag.tasks.reconciler import index_reconciler

def run_reconcile():
    print("Running reconciler locally...")
    try:
        index_reconciler.reconcile_all()
        print("Reconciliation completed successfully.")
    except Exception as e:
        print(f"Reconciliation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_reconcile()
