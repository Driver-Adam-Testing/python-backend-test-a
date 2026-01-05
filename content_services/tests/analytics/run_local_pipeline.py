#!/usr/bin/env python3
"""
Local test script for analytics pipeline.

Run from content_services directory:
    poetry run python tests/analytics/run_local_pipeline.py [local_repo_path]

Examples:
    poetry run python tests/analytics/run_local_pipeline.py
    poetry run python tests/analytics/run_local_pipeline.py /path/to/local/repo

This will:
1. Open the local repo (or use default test repo)
2. Run the analytics pipeline (export phase only - skips S3)
3. Output the JSON files for inspection
4. Print key fields to verify schema changes
"""
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pygit2

# Add src to path (go up two levels from tests/analytics/ to content_services/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from analytics.pipeline.phases.extract import extract_commits
from analytics.pipeline.phases.branches import discover_branches
from analytics.aggregation.engine import AggregationEngine
from analytics.export.exporter import DriverJSONExporter
from analytics.storage.hot_storage import HotStorage
from analytics.storage.parquet_storage import ParquetStorage


def main():
    # Parse command line args - expect a local path
    if len(sys.argv) > 1:
        repo_path = Path(sys.argv[1])
    else:
        # Default to the local analytics-test-repo
        repo_path = Path("/Users/adamtilton/work/driver/driver-adam-testing/analytics-test-repo")
    
    if not repo_path.exists():
        print(f"ERROR: Repository path does not exist: {repo_path}")
        return 1
    
    # Extract owner/name from path
    repo_name = repo_path.name
    repo_owner = repo_path.parent.name
    
    codebase_id = str(uuid.uuid4())
    
    print("=" * 60)
    print("Analytics Pipeline Local Test")
    print("=" * 60)
    print(f"Repo path: {repo_path}")
    print(f"Codebase ID: {codebase_id}")
    print(f"Owner: {repo_owner}")
    print(f"Name: {repo_name}")
    print()
    
    # Set up working directory
    work_dir = Path("/tmp/analytics_test")
    work_dir.mkdir(parents=True, exist_ok=True)
    
    storage_path = work_dir / codebase_id
    
    # Phase 1: Open repository
    print("Phase 1: Opening repository...")
    try:
        repo = pygit2.Repository(str(repo_path))
        print(f"  Opened: {repo_path}")
    except Exception as e:
        print(f"ERROR: Failed to open repository: {e}")
        return 1
    print()
    
    # Phase 2: Discover branches
    print("Phase 2: Discovering branches...")
    branches_result = discover_branches(repo)
    print(f"  Found {len(branches_result.branches)} branches")
    print(f"  Default branch: {branches_result.default_branch}")
    print()
    
    # Phase 3: Initialize storage
    print("Phase 3: Initializing storage...")
    hot_path = storage_path / "hot" / "analytics.duckdb"
    hot_path.parent.mkdir(parents=True, exist_ok=True)
    hot_storage = HotStorage(hot_path)
    hot_storage.connect()
    
    warm_path = storage_path / "warm"
    warm_storage = ParquetStorage(warm_path)
    
    cold_path = storage_path / "cold"
    cold_storage = ParquetStorage(cold_path)
    print(f"  Hot storage: {hot_path}")
    print(f"  Warm storage: {warm_path}")
    print(f"  Cold storage: {cold_path}")
    print()
    
    # Phase 4: Extract commits
    print("Phase 4: Extracting commits...")
    branch_names = [b.name for b in branches_result.branches]
    extract_result = extract_commits(
        repo=repo,
        codebase_id=codebase_id,
        branch_names=branch_names,
        include_patches=True,
        include_file_changes=True,
    )
    print(f"  Extracted {extract_result.total_commits} commits")
    
    # Store commits in warm storage
    if extract_result.commits:
        warm_storage.write_commits(codebase_id, extract_result.commits)
        print(f"  Stored {len(extract_result.commits)} commits in warm storage")
    
    # Store file changes in cold storage
    if extract_result.file_changes:
        cold_storage.write_file_changes(
            codebase_id=codebase_id,
            file_changes=extract_result.file_changes,
            partition_by_date=True,
        )
        print(f"  Stored {len(extract_result.file_changes)} file changes in cold storage")
    print()
    
    # Phase 5: Aggregate
    print("Phase 5: Aggregating metrics...")
    engine = AggregationEngine(hot_storage, warm_storage, cold_storage)
    engine._repo_name = repo_name
    engine._repo_owner = repo_owner
    engine.build_all_aggregates(
        codebase_id=codebase_id,
        force_rebuild=True,
        repo_owner=repo_owner,
        repo_name=repo_name,
    )
    print("  Aggregation complete")
    
    # Phase 6: Branch metrics
    print("Phase 6: Refreshing branch metrics...")
    branch_stats = engine.refresh_branch_metrics(codebase_id)
    print(f"  Refreshed {len(branch_stats.get('branches_updated', []))} branches")
    print()
    
    # Phase 7: Export JSON
    print("Phase 7: Exporting JSON...")
    json_dir = storage_path / "json"
    json_dir.mkdir(parents=True, exist_ok=True)
    
    exporter = DriverJSONExporter(
        codebase_id=codebase_id,
        hot_storage=hot_storage,
        warm_storage=warm_storage,
        cold_storage=cold_storage,
        output_dir=json_dir,
    )
    # Get last commit info from the extracted commits
    last_commit_sha = None
    last_commit_date = None
    if extract_result.commits:
        last_commit = extract_result.commits[0]  # First is most recent
        last_commit_sha = last_commit.get('commit_sha')
        last_commit_date = last_commit.get('committed_at')
    
    json_files = exporter.export_all(
        last_commit_sha=last_commit_sha,
        last_commit_date=last_commit_date,
        total_commits=extract_result.total_commits,
    )
    print(f"  Exported {len(json_files)} files to {json_dir}")
    print()
    
    # Display results
    print("=" * 60)
    print("Generated JSON Files")
    print("=" * 60)
    
    for json_file in sorted(json_dir.glob("*.json")):
        print(f"\n{'='*60}")
        print(f"--- {json_file.name} ---")
        print('='*60)
        with open(json_file) as f:
            data = json.load(f)
        
        # Highlight key fields for overview.json
        if json_file.name == "overview.json":
            print("\n🔑 KEY FIELDS (verify these are correct):")
            print(f"  primary_language:  {data.get('primary_language')}")
            print(f"  current_sloc:      {data.get('current_sloc')}")
            print(f"  current_lines:     {data.get('current_lines')}")
            print(f"  additions_lines:   {data.get('additions_lines')}")
            print(f"  deletions_lines:   {data.get('deletions_lines')}")
            print(f"  churn_lines:       {data.get('churn_lines')}")
            print(f"  net_lines:         {data.get('net_lines')}")
            print(f"  additions_sloc:    {data.get('additions_sloc')}")
            print(f"  deletions_sloc:    {data.get('deletions_sloc')}")
            print(f"  churn_sloc:        {data.get('churn_sloc')}")
            print(f"  net_sloc:          {data.get('net_sloc')}")
            
            # Check for OLD field names (should NOT exist)
            old_fields = ['total_churn', 'total_additions_lines', 'total_deletions_lines', 
                         'total_addition_bytes', 'total_deletion_bytes', 'total_sloc', 'total_lines']
            found_old = [f for f in old_fields if f in data]
            if found_old:
                print(f"\n⚠️  WARNING: Found OLD field names: {found_old}")
            else:
                print(f"\n✅ No old field names found - schema is correct!")
            
            print("\nFull JSON:")
        
        print(json.dumps(data, indent=2, default=str))
    
    # Also show what would go in codebases_list.json
    print("\n" + "=" * 60)
    print("Simulated codebases_list.json entry")
    print("=" * 60)
    metrics = hot_storage.get_repository_metrics(codebase_id)
    if metrics:
        # This simulates what orchestrator._phase_update_org_files would produce
        additions_sloc = metrics.get('additions_sloc', 0)
        deletions_sloc = metrics.get('deletions_sloc', 0)
        net_sloc = additions_sloc - deletions_sloc
        current_sloc = metrics.get('current_sloc', net_sloc)
        
        entry = {
            "codebase_id": codebase_id,
            "display_name": metrics.get('full_name', f"{repo_owner}/{repo_name}"),
            "full_name": metrics.get('full_name', f"{repo_owner}/{repo_name}"),
            "owner": repo_owner,
            "repository_name": repo_name,
            "total_commits": metrics.get('total_commits', 0),
            "total_contributors": metrics.get('total_contributors', 0),
            "total_branches": metrics.get('total_branches', 0),
            "churn_lines": metrics.get('churn_lines', 0),  # NEW field name
            "current_sloc": current_sloc,
            "net_sloc": net_sloc,
            "primary_language": metrics.get('primary_language'),
            "last_commit_date": str(metrics.get('last_commit_at')),
            "has_analytics": True,
            "analytics_status": "complete",
        }
        print(json.dumps(entry, indent=2, default=str))
        
        # Verify key fields
        print("\n🔑 KEY FIELDS for Admin Analytics table:")
        print(f"  churn_lines:       {entry['churn_lines']}")
        print(f"  primary_language:  {entry['primary_language']}")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
