import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.celery_tasks import reconcile_indexes_task

if __name__ == "__main__":
    print("Triggering reconcile_indexes_task...")
    try:
        # Run synchronously for debugging
        reconcile_indexes_task()
        print("reconcile_indexes_task completed.")
    except Exception as e:
        print(f"Error running reconcile_indexes_task: {e}")
        import traceback
        traceback.print_exc()
