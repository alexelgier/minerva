"""
Targeted diagnosis to identify the specific workflow validation issue
that's causing the Worker creation to fail.
"""

import asyncio
import traceback
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.client import Client

async def test_workflow_components_individually():
    """Test each component of the workflow individually to isolate the validation issue."""
    print("=" * 70)
    print("WORKFLOW VALIDATION DIAGNOSIS")
    print("=" * 70)

    # Test 1: Can we import the workflow class?
    try:
        print("\n🧪 Test 1: Importing workflow class...")
        from minerva_backend.processing.temporal_orchestrator import JournalProcessingWorkflow
        print("   ✅ Workflow class import successful")
    except Exception as e:
        print(f"   ❌ Workflow class import failed: {e}")
        traceback.print_exc()
        return

    # Test 2: Can we instantiate the workflow class?
    try:
        print("\n🧪 Test 2: Instantiating workflow class...")
        workflow_instance = JournalProcessingWorkflow()
        print("   ✅ Workflow instantiation successful")
    except Exception as e:
        print(f"   ❌ Workflow instantiation failed: {e}")
        traceback.print_exc()
        return

    # Test 3: Test workflow decorator validation
    try:
        print("\n🧪 Test 3: Checking workflow decorator...")
        # Check if the class has the proper workflow definition
        if hasattr(JournalProcessingWorkflow, '__temporal_workflow_definition'):
            print("   ✅ Workflow has proper @workflow.defn decorator")
        else:
            print("   ⚠️  Workflow missing __temporal_workflow_definition attribute")
    except Exception as e:
        print(f"   ❌ Workflow decorator check failed: {e}")
        traceback.print_exc()

    # Test 4: Test the run method specifically
    try:
        print("\n🧪 Test 4: Checking workflow run method...")
        if hasattr(workflow_instance, 'run'):
            print("   ✅ Workflow has run method")

            # Check if it's properly decorated
            if hasattr(workflow_instance.run, '__temporal_workflow_method_type'):
                print("   ✅ Run method has proper @workflow.run decorator")
            else:
                print("   ⚠️  Run method missing __temporal_workflow_method_type attribute")
        else:
            print("   ❌ Workflow missing run method")
    except Exception as e:
        print(f"   ❌ Run method check failed: {e}")
        traceback.print_exc()

    # Test 5: Test activity imports
    try:
        print("\n🧪 Test 5: Testing activity class import...")
        from minerva_backend.processing.temporal_orchestrator import PipelineActivities
        print("   ✅ Activity class import successful")
    except Exception as e:
        print(f"   ❌ Activity class import failed: {e}")
        traceback.print_exc()
        return

    # Test 6: Test model imports used in workflow
    try:
        print("\n🧪 Test 6: Testing model imports...")
        from minerva_backend.graph.models.documents import JournalEntry
        from minerva_backend.graph.models.entities import Entity
        from minerva_backend.graph.models.relations import Relation
        print("   ✅ All model imports successful")
    except Exception as e:
        print(f"   ❌ Model imports failed: {e}")
        traceback.print_exc()
        return

    # Test 7: Test creating a mock JournalEntry for type checking
    try:
        print("\n🧪 Test 7: Testing JournalEntry creation...")
        from datetime import datetime
        journal_entry = JournalEntry.from_text("sampletext", "1999-01-01")
        print("   ✅ JournalEntry creation successful")
    except Exception as e:
        print(f"   ❌ JournalEntry creation failed: {e}")
        traceback.print_exc()
        return

    # Test 8: Try minimal worker creation with just workflow (no activities)
    try:
        print("\n🧪 Test 8: Testing minimal worker creation (workflow only)...")

        client = await Client.connect("localhost:7233", data_converter=pydantic_data_converter)

        from temporalio.worker import Worker

        # Try creating worker with just the workflow, no activities
        worker = Worker(
            client,
            task_queue="test-queue",
            workflows=[JournalProcessingWorkflow],
            debug_mode=True
        )
        print("   ✅ Minimal worker creation successful")

    except Exception as e:
        print(f"   ❌ Minimal worker creation failed: {e}")
        print(f"   Full error: {traceback.format_exc()}")

        # Check if this is the validation error
        if "Failed validating workflow" in str(e):
            print("   🎯 FOUND IT! This is the workflow validation error")

            # Try to get more details
            try:
                # Get the underlying cause
                if hasattr(e, '__cause__') and e.__cause__:
                    print(f"   Root cause: {e.__cause__}")
                if hasattr(e, '__context__') and e.__context__:
                    print(f"   Context: {e.__context__}")
            except:
                pass

    print(f"\n{'='*70}")
    print("DIAGNOSIS COMPLETE")
    print("If Test 8 failed with 'Failed validating workflow', the issue is likely:")
    print("1. Missing or incorrect workflow decorators")
    print("2. Type annotation issues in the workflow run method")
    print("3. Import issues with Pydantic models")
    print("4. Circular import dependencies")
    print(f"{'='*70}")

if __name__ == "__main__":
    asyncio.run(test_workflow_components_individually())