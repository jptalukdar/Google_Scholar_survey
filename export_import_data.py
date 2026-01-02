#!/usr/bin/env python3
"""
SLR Extension Data Export/Import Utility

Export and import papers and projects for backup or transfer between machines.

Usage:
    python export_import_data.py export [output_file]
    python export_import_data.py import <input_file>
    python export_import_data.py export-csv [output_file]
"""

import json
import csv
import sys
import os
from datetime import datetime

DATA_FILE = "slr_extension_data.json"

def load_data():
    """Load data from the JSON storage file."""
    if not os.path.exists(DATA_FILE):
        return {"projects": [], "papers": [], "query_history": {}}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading data: {e}")
        return {"projects": [], "papers": [], "query_history": {}}

def save_data(data):
    """Save data to the JSON storage file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Data saved to {DATA_FILE}")

def export_json(output_file=None):
    """Export all data to a JSON file."""
    data = load_data()
    
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"slr_export_{timestamp}.json"
    
    export_data = {
        "exported_at": datetime.now().isoformat(),
        "version": "1.0",
        "projects": data.get("projects", []),
        "papers": data.get("papers", []),
        "query_history": data.get("query_history", {})
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    stats = {
        "projects": len(export_data["projects"]),
        "papers": len(export_data["papers"]),
        "queries": sum(len(v) for v in export_data["query_history"].values())
    }
    
    print(f"Exported to: {output_file}")
    print(f"  - {stats['projects']} projects")
    print(f"  - {stats['papers']} papers")
    print(f"  - {stats['queries']} query history entries")
    
    return output_file

def export_csv(output_file=None):
    """Export papers to CSV format."""
    data = load_data()
    papers = data.get("papers", [])
    
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"slr_papers_{timestamp}.csv"
    
    if not papers:
        print("No papers to export.")
        return None
    
    fieldnames = ["id", "title", "authors", "url", "pdfUrl", "abstract", "source", "project_id", "status"]
    
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for paper in papers:
            writer.writerow(paper)
    
    print(f"Exported {len(papers)} papers to: {output_file}")
    return output_file

def import_json(input_file):
    """Import data from a JSON file."""
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        return False
    
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            import_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON file: {e}")
        return False
    
    # Load existing data
    existing = load_data()
    
    # Merge projects (avoid duplicates by ID)
    existing_project_ids = {p["id"] for p in existing.get("projects", [])}
    new_projects = [p for p in import_data.get("projects", []) if p["id"] not in existing_project_ids]
    existing["projects"] = existing.get("projects", []) + new_projects
    
    # Merge papers (avoid duplicates by ID)
    existing_paper_ids = {p["id"] for p in existing.get("papers", [])}
    new_papers = [p for p in import_data.get("papers", []) if p["id"] not in existing_paper_ids]
    existing["papers"] = existing.get("papers", []) + new_papers
    
    # Merge query history
    if "query_history" not in existing:
        existing["query_history"] = {}
    for project_id, queries in import_data.get("query_history", {}).items():
        if project_id not in existing["query_history"]:
            existing["query_history"][project_id] = queries
        else:
            # Avoid duplicate queries
            existing_queries = {q["query"] for q in existing["query_history"][project_id]}
            new_queries = [q for q in queries if q["query"] not in existing_queries]
            existing["query_history"][project_id] = new_queries + existing["query_history"][project_id]
    
    save_data(existing)
    
    print(f"Import complete!")
    print(f"  - Added {len(new_projects)} new projects")
    print(f"  - Added {len(new_papers)} new papers")
    
    return True

def show_stats():
    """Show current database statistics."""
    data = load_data()
    
    print("\n=== SLR Database Statistics ===")
    print(f"Projects: {len(data.get('projects', []))}")
    print(f"Papers:   {len(data.get('papers', []))}")
    
    # Papers by project
    papers_by_project = {}
    for paper in data.get("papers", []):
        pid = paper.get("project_id", "default")
        papers_by_project[pid] = papers_by_project.get(pid, 0) + 1
    
    if papers_by_project:
        print("\nPapers by project:")
        for pid, count in papers_by_project.items():
            print(f"  - {pid}: {count} papers")
    
    # Query history
    qh = data.get("query_history", {})
    total_queries = sum(len(v) for v in qh.values())
    print(f"\nQuery history: {total_queries} entries across {len(qh)} projects")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        show_stats()
        return
    
    command = sys.argv[1].lower()
    
    if command == "export":
        output = sys.argv[2] if len(sys.argv) > 2 else None
        export_json(output)
    
    elif command == "export-csv":
        output = sys.argv[2] if len(sys.argv) > 2 else None
        export_csv(output)
    
    elif command == "import":
        if len(sys.argv) < 3:
            print("Error: Please specify input file")
            print("Usage: python export_import_data.py import <input_file>")
            return
        import_json(sys.argv[2])
    
    elif command == "stats":
        show_stats()
    
    else:
        print(f"Unknown command: {command}")
        print(__doc__)

if __name__ == "__main__":
    main()
