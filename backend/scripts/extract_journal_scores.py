#!/usr/bin/env python3
"""
Extract Journal Scores to DataFrame Script

This script processes all markdown journal files from a specified directory,
extracts wellbeing scores using the existing JournalEntry parsing logic,
and outputs a comprehensive pandas DataFrame with both raw individual scores
and computed scaled metrics.

Usage:
    python extract_journal_scores.py [directory_path]
    
    If no directory is provided, defaults to "D:\\yo\\02 - Daily Notes"
"""

import sys
import warnings
from pathlib import Path
from datetime import date
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np

# Add the src directory to the path to import minerva_backend modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from minerva_backend.graph.models.documents import JournalEntry


def extract_date_from_filename(filename: str) -> Optional[date]:
    """Extract date from filename in format YYYY-MM-DD.md"""
    try:
        # Remove .md extension and parse date
        date_str = filename.replace('.md', '')
        year, month, day = date_str.split('-')
        return date(int(year), int(month), int(day))
    except (ValueError, AttributeError):
        return None


def calculate_scaled_scores(panas_pos: Optional[List[float]], 
                          panas_neg: Optional[List[float]], 
                          bpns: Optional[List[float]], 
                          flourishing: Optional[List[float]]) -> Dict[str, float]:
    """Calculate scaled scores using the formulas from journal markdown files"""
    scores = {}
    
    # PANAS Positive scaled: (sum - 10) / (50 - 10) * 100
    if panas_pos and len(panas_pos) == 10:
        panas_pos_sum = sum(panas_pos)
        scores['panas_pos_scaled'] = (panas_pos_sum - 10) / (50 - 10) * 100
    else:
        scores['panas_pos_scaled'] = np.nan
    
    # PANAS Negative scaled: (sum - 10) / (50 - 10) * 100
    if panas_neg and len(panas_neg) == 10:
        panas_neg_sum = sum(panas_neg)
        scores['panas_neg_scaled'] = (panas_neg_sum - 10) / (50 - 10) * 100
    else:
        scores['panas_neg_scaled'] = np.nan
    
    # BPNS scores (7 items total: 2 autonomy + 2 competence + 3 relatedness)
    if bpns and len(bpns) == 7:
        autonomy_sum = bpns[0] + bpns[1]  # First 2 items
        competence_sum = bpns[2] + bpns[3]  # Next 2 items
        relatedness_sum = bpns[4] + bpns[5] + bpns[6]  # Last 3 items
        bpns_total = autonomy_sum + competence_sum + relatedness_sum
        
        # Individual scaled scores
        scores['bpns_autonomy_scaled'] = (autonomy_sum - 2) / (14 - 2) * 100
        scores['bpns_competence_scaled'] = (competence_sum - 2) / (14 - 2) * 100
        scores['bpns_relatedness_scaled'] = (relatedness_sum - 3) / (21 - 3) * 100
        scores['bpns_total_scaled'] = (bpns_total - 7) / (49 - 7) * 100
    else:
        scores['bpns_autonomy_scaled'] = np.nan
        scores['bpns_competence_scaled'] = np.nan
        scores['bpns_relatedness_scaled'] = np.nan
        scores['bpns_total_scaled'] = np.nan
    
    # Flourishing scaled: (sum - 8) / (56 - 8) * 100
    if flourishing and len(flourishing) == 8:
        flourishing_sum = sum(flourishing)
        scores['flourishing_scaled'] = (flourishing_sum - 8) / (56 - 8) * 100
    else:
        scores['flourishing_scaled'] = np.nan
    
    return scores


def extract_raw_scores(panas_pos: Optional[List[float]], 
                      panas_neg: Optional[List[float]], 
                      bpns: Optional[List[float]], 
                      flourishing: Optional[List[float]]) -> Dict[str, Any]:
    """Extract individual raw scores into separate columns"""
    scores = {}
    
    # PANAS Positive scores (10 items)
    panas_pos_labels = ['interested', 'excited', 'strong', 'enthusiastic', 'proud', 
                       'alert', 'inspired', 'determined', 'attentive', 'active']
    if panas_pos and len(panas_pos) == 10:
        for i, label in enumerate(panas_pos_labels):
            scores[f'panas_pos_{label}'] = panas_pos[i]
    else:
        for label in panas_pos_labels:
            scores[f'panas_pos_{label}'] = np.nan
    
    # PANAS Negative scores (10 items)
    panas_neg_labels = ['distressed', 'upset', 'guilty', 'scared', 'hostile', 
                       'irritable', 'ashamed', 'nervous', 'jittery', 'afraid']
    if panas_neg and len(panas_neg) == 10:
        for i, label in enumerate(panas_neg_labels):
            scores[f'panas_neg_{label}'] = panas_neg[i]
    else:
        for label in panas_neg_labels:
            scores[f'panas_neg_{label}'] = np.nan
    
    # BPNS scores (7 items)
    bpns_labels = ['autonomy_choices', 'autonomy_tasks', 'competence_capable', 
                  'competence_challenges', 'relatedness_connected', 'relatedness_along', 
                  'relatedness_supported']
    if bpns and len(bpns) == 7:
        for i, label in enumerate(bpns_labels):
            scores[f'bpns_{label}'] = bpns[i]
    else:
        for label in bpns_labels:
            scores[f'bpns_{label}'] = np.nan
    
    # Flourishing scores (8 items)
    flourishing_labels = ['purposeful', 'relationships', 'engaged', 'contribute', 
                         'competent', 'good_person', 'optimistic', 'respected']
    if flourishing and len(flourishing) == 8:
        for i, label in enumerate(flourishing_labels):
            scores[f'flourishing_{label}'] = flourishing[i]
    else:
        for label in flourishing_labels:
            scores[f'flourishing_{label}'] = np.nan
    
    return scores


def process_journal_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Process a single journal file and extract all scores"""
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract date from filename
        journal_date = extract_date_from_filename(file_path.name)
        if not journal_date:
            print(f"WARNING: Could not extract date from filename: {file_path.name}")
            return None
        
        # Parse journal entry using existing JournalEntry logic
        journal_entry = JournalEntry.from_text(content, journal_date.isoformat())
        
        # Prepare result dictionary
        result = {'date': journal_date}
        
        # Check for missing scores and print warnings
        filename = file_path.name
        if not journal_entry.panas_pos:
            print(f"WARNING: Missing PANAS positive scores for {filename}")
        if not journal_entry.panas_neg:
            print(f"WARNING: Missing PANAS negative scores for {filename}")
        if not journal_entry.bpns:
            print(f"WARNING: Missing BPNS scores for {filename}")
        if not journal_entry.flourishing:
            print(f"WARNING: Missing Flourishing scores for {filename}")
        
        # Extract raw scores
        raw_scores = extract_raw_scores(
            journal_entry.panas_pos,
            journal_entry.panas_neg,
            journal_entry.bpns,
            journal_entry.flourishing
        )
        result.update(raw_scores)
        
        # Calculate scaled scores
        scaled_scores = calculate_scaled_scores(
            journal_entry.panas_pos,
            journal_entry.panas_neg,
            journal_entry.bpns,
            journal_entry.flourishing
        )
        result.update(scaled_scores)
        
        return result
        
    except Exception as e:
        print(f"ERROR: Failed to process {file_path.name}: {e}")
        return None


def main():
    """Main function to process all journal files and create DataFrame"""
    # Get directory path from command line or use default
    if len(sys.argv) > 1:
        directory_path = Path(sys.argv[1])
    else:
        directory_path = Path(r"D:\yo\02 - Daily Notes")
    
    if not directory_path.exists():
        print(f"ERROR: Directory does not exist: {directory_path}")
        return
    
    print(f"Processing journal files from: {directory_path}")
    
    # Find all .md files
    md_files = list(directory_path.glob("*.md"))
    if not md_files:
        print("No .md files found in the directory")
        return
    
    print(f"Found {len(md_files)} markdown files")
    
    # Process each file
    all_scores = []
    for file_path in sorted(md_files):
        print(f"Processing: {file_path.name}")
        scores = process_journal_file(file_path)
        if scores:
            all_scores.append(scores)
    
    if not all_scores:
        print("No valid journal entries found")
        return
    
    # Create DataFrame
    df = pd.DataFrame(all_scores)
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    print(f"\nSuccessfully processed {len(df)} journal entries")
    print(f"DataFrame shape: {df.shape}")
    
    # Display basic info
    print("\nDataFrame Info:")
    print(df.info())
    
    # Display first few rows
    print("\nFirst 5 rows:")
    print(df.head())
    
    # Save to CSV
    output_file = Path(__file__).parent / "journal_scores.csv"
    df.to_csv(output_file, index=False)
    print(f"\nDataFrame saved to: {output_file}")
    
    # Display summary statistics for scaled scores
    scaled_columns = [col for col in df.columns if col.endswith('_scaled')]
    if scaled_columns:
        print(f"\nSummary statistics for scaled scores:")
        print(df[scaled_columns].describe())


if __name__ == "__main__":
    main()
