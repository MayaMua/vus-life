import os
import sys
import pandas as pd
import re
from tqdm import tqdm
from typing import Optional, Tuple

# Add the backend directory to the Python path to enable package imports
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from tools.variant_processor.hgvs_g_to_vcf import hgvs_g_to_vcf
from tools.variant_processor.hgvs_c_to_g import convert_cdna_to_genomic_hgvs_mutalyzer


def normalize_cdna_notation(name_str):
    """
    Normalize cDNA notation by removing gene name in parentheses.
    
    Examples:
    - "NM_000051.4(ATM):c.-174A>G" -> "NM_000051.4:c.-174A>G"
    - "NM_000051.4:c.4415T>A" -> "NM_000051.4:c.4415T>A" (no change)
    - "NC_000011.10:g.108222768C>T" -> "NC_000011.10:g.108222768C>T" (genomic, no change)
    
    Parameters:
    - name_str: The Name column value from ClinVar
    
    Returns:
    - Normalized notation string
    """
    if not name_str or pd.isna(name_str):
        return None
    
    name_str = str(name_str).strip()
    
    # Check if it contains gene name in parentheses: NM_...(GENE):c....
    # Pattern: capture NM_accession, skip (gene), keep :c.variant
    match = re.match(r'(NM_[^(]+)\([^)]+\)(:.+)', name_str)
    if match:
        # Remove the gene name part
        return match.group(1) + match.group(2)
    
    # If no gene name pattern, return as is
    return name_str


def clean_protein_annotation(hgvs_str):
    """
    Remove protein annotation from HGVS notation.
    
    Many ClinVar entries include protein-level changes like (p.Met1Leu) which
    interfere with cDNA to genomic conversion. This function removes them.
    
    Examples:
    - "NM_000051.4:c.1A>T (p.Met1Leu)" -> "NM_000051.4:c.1A>T"
    - "NM_000051.4:c.-174A>G" -> "NM_000051.4:c.-174A>G" (no change)
    
    Parameters:
    - hgvs_str: HGVS notation string (possibly with protein annotation)
    
    Returns:
    - Cleaned HGVS notation string
    """
    if not hgvs_str or pd.isna(hgvs_str):
        return hgvs_str
    
    hgvs_str = str(hgvs_str).strip()
    
    # Remove protein annotation: (p.xxx) or ( p.xxx ) with optional spaces
    hgvs_str = re.sub(r'\s*\(p\.[^)]+\)\s*', '', hgvs_str)
    
    return hgvs_str.strip()


def classify_pathogenicity(pathogenicity_str):
    """
    Classify pathogenicity into clear categories.
    Returns 'pathogenic', 'benign', or None for mixed/unclear cases.
    
    Parameters:
    - pathogenicity_str: The Germline classification value
    
    Returns:
    - 'pathogenic', 'benign', or None
    """
    if not pathogenicity_str or pd.isna(pathogenicity_str):
        return None
    
    path_lower = str(pathogenicity_str).lower()
    
    # Check for clear pathogenic cases (no benign, no VUS, no conflicting)
    if "pathogenic" in path_lower and "benign" not in path_lower and "uncertain" not in path_lower and "conflicting" not in path_lower:
        return "pathogenic"
    
    # Check for clear benign cases (no pathogenic, no VUS, no conflicting)
    if "benign" in path_lower and "pathogenic" not in path_lower and "uncertain" not in path_lower and "conflicting" not in path_lower:
        return "benign"
    
    # Mixed or unclear cases
    return None


def parse_spdi_to_variant_components(spdi_notation: str) -> Tuple[Optional[str], Optional[int], Optional[str], Optional[str]]:
    """
    Parse SPDI notation to extract chromosome, position, ref, and alt alleles.
    
    SPDI format: Sequence:Position:Deletion:Insertion
    - Position is 0-based
    - Deletion: bases being deleted/replaced
    - Insertion: bases being inserted/replaced with
    
    Args:
        spdi_notation: SPDI notation string (e.g., "NC_000015.10:48645780:G:A")
        
    Returns:
        tuple: (chromosome, position, ref_allele, alt_allele) or (None, None, None, None)
    """
    if not isinstance(spdi_notation, str) or not spdi_notation.strip():
        return None, None, None, None
        
    # Regex to parse SPDI: Sequence:Position:Deletion:Insertion
    # Allow empty deletion/insertion for indels
    match = re.match(r"^(NC_\d+\.\d+):(\d+):([ACGT]*):([ACGT]*)$", spdi_notation)
    
    if match:
        sequence, pos_0based_str, deletion, insertion = match.groups()
        pos_0based = int(pos_0based_str)
        
        # Extract chromosome number from NC_000015.10 format
        chrom_match = re.match(r"NC_0*(\d+)\.\d+", sequence)
        if chrom_match:
            chromosome = chrom_match.group(1)
        else:
            chromosome = sequence  # Fallback to full sequence
        
        # For 1-based position (database storage)
        position = pos_0based + 1
        
        # Handle different SPDI types
        if deletion and insertion:
            # Substitution or complex variant
            ref_allele = deletion
            alt_allele = insertion
        elif deletion and not insertion:
            # Deletion
            ref_allele = deletion
            alt_allele = ""
        elif not deletion and insertion:
            # Insertion
            ref_allele = ""
            alt_allele = insertion
        else:
            # No change (shouldn't happen in practice)
            ref_allele = ""
            alt_allele = ""
        
        return chromosome, position, ref_allele, alt_allele
    else:
        return None, None, None, None


def parse_spdi_to_vcf_with_anchor(spdi_notation: str) -> Optional[dict]:
    """
    Converts SPDI notation to VCF format using SPDI's sequence information.
    Only fetches anchor bases (single positions) from NCBI when needed for indels.
    
    SPDI format: Sequence:Position:Deletion:Insertion
    - Position is 0-based
    - Deletion: reference bases being deleted/replaced (from SPDI!)
    - Insertion: bases being inserted/replaced with
    
    Args:
        spdi_notation: SPDI notation string (e.g., "NC_000011.10:108227637:TTAATGAT:")
        
    Returns:
        dict: VCF dictionary with keys (chrom, pos, ref, alt), or None if conversion fails
    """
    if not isinstance(spdi_notation, str) or not spdi_notation.strip():
        return None
        
    # Parse SPDI components
    match = re.match(r"^(NC_\d+\.\d+):(\d+):([ACGT]*):([ACGT]*)$", spdi_notation)
    
    if not match:
        return None
    
    sequence, pos_0based_str, deletion, insertion = match.groups()
    pos_0based = int(pos_0based_str)
    accession = sequence
    
    # Extract chromosome number from NC_000015.10 format
    chrom_match = re.match(r"NC_0*(\d+)\.\d+", sequence)
    if chrom_match:
        chromosome = int(chrom_match.group(1))
    else:
        return None  # Can't extract chromosome
    
    try:
        # Import here to avoid circular dependency and only when needed
        from tools.variant_processor.hgvs_g_to_vcf import get_reference_base
        
        # VCF uses 1-based positions and requires anchor bases for indels
        
        if deletion and insertion:
            # Substitution or complex variant (delins)
            if len(deletion) == 1 and len(insertion) == 1:
                # Simple SNP: no anchor needed
                vcf_pos = pos_0based + 1
                ref = deletion
                alt = insertion
            else:
                # Complex delins: needs anchor base
                anchor_pos = pos_0based  # 0-based in SPDI, but get_reference_base expects 1-based
                anchor = get_reference_base(accession, anchor_pos)
                vcf_pos = anchor_pos
                ref = anchor + deletion
                alt = anchor + insertion
                
        elif deletion and not insertion:
            # Pure deletion: VCF needs anchor base before deletion
            # SPDI has the deleted sequence, we just need the anchor
            anchor_pos = pos_0based  # Position before deletion
            anchor = get_reference_base(accession, anchor_pos)
            vcf_pos = anchor_pos
            ref = anchor + deletion
            alt = anchor
            
        elif not deletion and insertion:
            # Pure insertion: VCF needs anchor base
            anchor_pos = pos_0based
            anchor = get_reference_base(accession, anchor_pos)
            vcf_pos = anchor_pos
            ref = anchor
            alt = anchor + insertion
            
        else:
            # No change (shouldn't happen)
            return None
        
        return {
            'chrom': chromosome,
            'pos': vcf_pos,
            'ref': ref,
            'alt': alt
        }
    except Exception as e:
        # If fetching anchor base fails, return None
        return None


def parse_spdi_to_genomic_hgvs_grch38(spdi_notation: str) -> Optional[str]:
    """
    Converts SPDI notation to GRCh38 genomic HGVS (g. format).
    Handles substitutions, deletions, and insertions.
    
    SPDI format: Sequence:Position:Deletion:Insertion
    - For substitutions: NC_000011.10:108222767:C:T -> NC_000011.10:g.108222768C>T
    - For deletions: NC_000011.10:108227637:TTAATGAT: -> NC_000011.10:g.108227638_108227645del
    - For insertions: NC_000011.10:108227639::AAA -> NC_000011.10:g.108227639_108227640insAAA
    
    Args:
        spdi_notation: SPDI notation string
        
    Returns:
        str: Genomic HGVS notation, or None if conversion not possible
    """
    if not isinstance(spdi_notation, str) or not spdi_notation.strip():
        return None
        
    # Parse SPDI components
    match = re.match(r"^(NC_\d+\.\d+):(\d+):([ACGT]*):([ACGT]*)$", spdi_notation)
    
    if not match:
        return None
    
    sequence, pos_0based_str, deletion, insertion = match.groups()
    pos_0based = int(pos_0based_str)
    
    # For HGVS, position is 1-based
    pos_1based = pos_0based + 1
    
    # Handle different variant types
    if deletion and insertion:
        # Substitution or complex variant
        if len(deletion) == 1 and len(insertion) == 1:
            # Simple substitution: g.108222768C>T
            genomic_hgvs = f"{sequence}:g.{pos_1based}{deletion}>{insertion}"
        elif len(deletion) == len(insertion):
            # Multi-base substitution: g.108222768_108222770delinsABC
            end_pos = pos_1based + len(deletion) - 1
            genomic_hgvs = f"{sequence}:g.{pos_1based}_{end_pos}delins{insertion}"
        else:
            # Complex indel
            end_pos = pos_1based + len(deletion) - 1
            genomic_hgvs = f"{sequence}:g.{pos_1based}_{end_pos}delins{insertion}"
    elif deletion and not insertion:
        # Deletion
        if len(deletion) == 1:
            # Single base deletion: g.108227638del
            genomic_hgvs = f"{sequence}:g.{pos_1based}del"
        else:
            # Multi-base deletion: g.108227638_108227645del
            end_pos = pos_1based + len(deletion) - 1
            genomic_hgvs = f"{sequence}:g.{pos_1based}_{end_pos}del"
    elif not deletion and insertion:
        # Insertion: g.108227639_108227640insAAA
        end_pos = pos_1based + 1
        genomic_hgvs = f"{sequence}:g.{pos_1based}_{end_pos}ins{insertion}"
    else:
        # No change (shouldn't happen)
        return None
    
    return genomic_hgvs


def process_clinvar(input_file, output_file, 
                    gene_symbol, 
                    genomic_accession, 
                    test_rows=0,
                    batch_size=100,
                    save_checkpoints=False):
    """
    Process ClinVar data in simplified format with batch processing.
    
    Parameters:
    - input_file: Path to ClinVar txt file
    - output_file: Path to output CSV file
    - gene_symbol: Gene symbol to add to results
    - genomic_accession: Genomic accession for the gene (e.g., "NC_000011.10" for ATM)
    - test_rows: Number of rows to process for testing (0 for all)
    - batch_size: Number of variants to process per batch (default: 100)
    - save_checkpoints: If True, save intermediate results after each batch
    """
    print(f"Reading ClinVar data from: {input_file}")
    
    # Read the tab-separated file
    df = pd.read_csv(input_file, sep='\t', low_memory=False)
    
    print(f"Total rows in file: {len(df)}")
    print(f"Columns: {df.columns.tolist()}")
    
    # Select required columns: Name, Canonical SPDI, and Germline classification
    columns_required = ['Name', 'Canonical SPDI', 'Germline classification']
    df = df[columns_required].copy()
    
    # For testing, take first N rows
    if test_rows:
        df = df.head(test_rows).copy()
        print(f"\nProcessing first {test_rows} rows for testing")
    
    print(f"\nSample data:")
    print(df.head())
    
    # Filter by pathogenicity
    print("\nFiltering by pathogenicity...")
    df['pathogenicity_original'] = df['Germline classification'].apply(classify_pathogenicity)
    df_filtered = df[df['pathogenicity_original'].notna()].copy()
    
    print(f"Rows after pathogenicity filter: {len(df_filtered)}")
    if len(df_filtered) == 0:
        print("Warning: No rows passed pathogenicity filter!")
        return
    
    print(f"\nPathogenicity distribution:")
    print(df_filtered['pathogenicity_original'].value_counts())
    
    # Step 1: Try to parse SPDI notation first
    print("\nParsing SPDI notation to genomic HGVS...")
    df_filtered['hgvs_genomic_38_spdi'] = df_filtered['Canonical SPDI'].apply(parse_spdi_to_genomic_hgvs_grch38)
    
    spdi_success = df_filtered['hgvs_genomic_38_spdi'].notna().sum()
    print(f"  Successfully parsed {spdi_success}/{len(df_filtered)} variants from SPDI")
    
    # Step 2: For failed SPDI parsing, prepare cDNA fallback
    print("\nPreparing cDNA fallback for failed SPDI parsing...")
    df_filtered['hgvs_coding'] = df_filtered['Name'].apply(normalize_cdna_notation)
    df_filtered['hgvs_coding'] = df_filtered['hgvs_coding'].apply(clean_protein_annotation)
    
    # Identify rows that need cDNA conversion (SPDI failed AND has cDNA notation)
    needs_cdna_conversion = (
        df_filtered['hgvs_genomic_38_spdi'].isna() & 
        df_filtered['hgvs_coding'].str.contains(':c.', na=False)
    )
    
    cdna_conversion_count = needs_cdna_conversion.sum()
    print(f"  {cdna_conversion_count} variants need cDNA to genomic conversion")
    
    if cdna_conversion_count > 0:
        print("\nSample cDNA notations to convert:")
        print(df_filtered[needs_cdna_conversion][['Name', 'hgvs_coding']].head())
        
        # Convert cDNA to genomic HGVS in batches
        print(f"\nConverting cDNA to genomic HGVS (GRCh38)...")
        print(f"Using genomic accession: {genomic_accession}")
        
        cdna_indices = df_filtered[needs_cdna_conversion].index.tolist()
        total_variants = len(cdna_indices)
        num_batches = (total_variants + batch_size - 1) // batch_size
        
        print(f"Processing {total_variants} variants in {num_batches} batches of {batch_size}")
        if save_checkpoints:
            print(f"Checkpoint mode: Intermediate results will be saved after each batch")
        
        hgvs_genomic_cdna_dict = {}
        failed_examples = []
        
        # Process in batches
        for batch_num in range(num_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, total_variants)
            current_batch_size = end_idx - start_idx
            
            print(f"\nBatch {batch_num + 1}/{num_batches}: Processing variants {start_idx + 1}-{end_idx}")
            
            # Get batch indices
            batch_indices = cdna_indices[start_idx:end_idx]
            
            # Process batch with progress bar
            batch_results = {}
            for idx in tqdm(batch_indices, desc=f"Batch {batch_num + 1}", total=current_batch_size):
                hgvs_c = df_filtered.loc[idx, 'hgvs_coding']
                
                if hgvs_c and ':c.' in hgvs_c:
                    # Parse the cDNA notation to extract transcript and variant
                    # Format: NM_000051.4:c.-174A>G
                    parts = hgvs_c.split(':', 1)
                    if len(parts) == 2:
                        transcript_acc = parts[0]  # NM_000051.4
                        cdna_variant = parts[1]    # c.-174A>G
                        
                        # Call with three parameters: transcript, cdna, genomic
                        # Results are automatically cached by @disk_cache.memoize()
                        hgvs_g = convert_cdna_to_genomic_hgvs_mutalyzer(
                            transcript_acc, 
                            cdna_variant, 
                            genomic_accession
                        )
                    else:
                        hgvs_g = None
                    
                    if hgvs_g is None and len(failed_examples) < 3:
                        failed_examples.append(hgvs_c)
                else:
                    hgvs_g = None
                
                batch_results[idx] = hgvs_g
            
            # Add batch results to dict
            hgvs_genomic_cdna_dict.update(batch_results)
            
            # Show batch statistics
            batch_success = sum(1 for x in batch_results.values() if x is not None)
            batch_failed = current_batch_size - batch_success
            print(f"  Batch {batch_num + 1} complete: {batch_success} success, {batch_failed} failed")
        
        # Merge cDNA conversion results
        df_filtered['hgvs_genomic_38_cdna'] = df_filtered.index.map(hgvs_genomic_cdna_dict)
        
        if failed_examples:
            print(f"\nSample failed cDNA conversions:")
            for example in failed_examples:
                print(f"  {example}")
    else:
        df_filtered['hgvs_genomic_38_cdna'] = None
    
    # Combine SPDI and cDNA results (prefer SPDI, fallback to cDNA)
    print("\nCombining SPDI and cDNA conversion results...")
    df_filtered['hgvs_genomic_38'] = df_filtered['hgvs_genomic_38_spdi'].fillna(df_filtered['hgvs_genomic_38_cdna'])
    
    # Track conversion method for debugging
    df_filtered['conversion_method'] = 'none'
    df_filtered.loc[df_filtered['hgvs_genomic_38_spdi'].notna(), 'conversion_method'] = 'spdi'
    df_filtered.loc[
        (df_filtered['hgvs_genomic_38_spdi'].isna()) & 
        (df_filtered['hgvs_genomic_38_cdna'].notna()), 
        'conversion_method'
    ] = 'cdna'
    
    print(f"\nConversion method distribution:")
    print(df_filtered['conversion_method'].value_counts())
    
    # Debug: Check overall conversion results
    print(f"\nOverall genomic HGVS conversion results:")
    print(f"  Success: {df_filtered['hgvs_genomic_38'].notna().sum()}/{len(df_filtered)}")
    print(f"  Failed: {df_filtered['hgvs_genomic_38'].isna().sum()}/{len(df_filtered)}")
    
    # List failed conversions
    failed_df = df_filtered[df_filtered['hgvs_genomic_38'].isna()].copy()
    if len(failed_df) > 0:
        print(f"\nFailed HGVS conversions ({len(failed_df)} variants):")
        print("-" * 80)
        for idx, row in failed_df.iterrows():
            name = row.get('Name', 'N/A')
            spdi = row.get('Canonical SPDI', 'N/A')
            hgvs_coding = row.get('hgvs_coding', 'N/A')
            print(f"  Name: {name}")
            print(f"  SPDI: {spdi}")
            print(f"  cDNA: {hgvs_coding}")
            print()
    
    # Filter out failed conversions
    df_filtered = df_filtered[df_filtered['hgvs_genomic_38'].notna()].copy()
    
    if len(df_filtered) == 0:
        print("Warning: No successful genomic HGVS conversions!")
        return
    
    print(f"\nSample genomic HGVS:")
    print(df_filtered[['Name', 'Canonical SPDI', 'hgvs_genomic_38', 'conversion_method']].head(10))
    
    # Process checkpoint saving if needed
    if save_checkpoints and cdna_conversion_count > 0:
            # Create checkpoint filename
            checkpoint_file = output_file.replace('.csv', f'_checkpoint_batch{batch_num + 1}.csv')
            
            # Save checkpoint with partial results (only variants successfully converted so far)
            checkpoint_df = df_filtered[df_filtered['hgvs_genomic_38'].notna()].copy()
            
            if len(checkpoint_df) > 0:
                # Parse VCF for checkpoint
                vcf_results_checkpoint = []
                for hgvs_g in checkpoint_df['hgvs_genomic_38']:
                    vcf = hgvs_g_to_vcf(hgvs_g)
                    vcf_results_checkpoint.append(vcf)
                
                vcf_df_checkpoint = pd.DataFrame([
                    {
                        'chromosome': vcf.get('chrom') if vcf else None,
                        'position': vcf.get('pos') if vcf else None,
                        'ref_allele': vcf.get('ref') if vcf else None,
                        'alt_allele': vcf.get('alt') if vcf else None
                    }
                    for vcf in vcf_results_checkpoint
                ], index=checkpoint_df.index)
                
                checkpoint_df[['chromosome', 'position', 'ref_allele', 'alt_allele']] = vcf_df_checkpoint
                checkpoint_df['gene_symbol'] = gene_symbol
                
                output_columns = [
                    'hgvs_genomic_38',
                    'hgvs_coding',
                    'chromosome',
                    'position',
                    'ref_allele',
                    'alt_allele',
                    'gene_symbol',
                    'pathogenicity_original'
                ]
                
                checkpoint_output = checkpoint_df[output_columns].copy()
                checkpoint_output = checkpoint_output[checkpoint_output['chromosome'].notna()].copy()
                
                os.makedirs(os.path.dirname(checkpoint_file), exist_ok=True)
                checkpoint_output.to_csv(checkpoint_file, index=False)
                print(f"  Checkpoint saved: {checkpoint_file} ({len(checkpoint_output)} variants)")
    
    # Convert to VCF format - try SPDI first, then fall back to HGVS
    print("\nConverting to VCF format...")
    print("  Step 1: Trying SPDI-based conversion (uses SPDI sequences, minimal network calls)...")
    
    vcf_results = []
    vcf_indices = []
    spdi_success_count = 0
    
    for idx in tqdm(df_filtered.index, desc="SPDI to VCF"):
        spdi = df_filtered.loc[idx, 'Canonical SPDI']
        
        # Try SPDI-based conversion first (more efficient)
        vcf = None
        if pd.notna(spdi) and spdi:
            vcf = parse_spdi_to_vcf_with_anchor(spdi)
            if vcf:
                spdi_success_count += 1
        
        vcf_results.append(vcf)
        vcf_indices.append(idx)
    
    print(f"  SPDI conversion: {spdi_success_count}/{len(df_filtered)} succeeded")
    
    # For failed SPDI conversions, try HGVS genomic conversion
    failed_indices = [i for i, vcf in enumerate(vcf_results) if vcf is None]
    if failed_indices:
        print(f"  Step 2: Trying HGVS genomic conversion for {len(failed_indices)} failed variants...")
        
        for i in tqdm(failed_indices, desc="HGVS to VCF"):
            idx = vcf_indices[i]
            hgvs_g = df_filtered.loc[idx, 'hgvs_genomic_38']
            vcf = hgvs_g_to_vcf(hgvs_g)
            vcf_results[i] = vcf
    
    # Parse VCF dictionary into separate columns in a single pass
    vcf_df = pd.DataFrame([
        {
            'chromosome': vcf.get('chrom') if vcf else None,
            'position': vcf.get('pos') if vcf else None,
            'ref_allele': vcf.get('ref') if vcf else None,
            'alt_allele': vcf.get('alt') if vcf else None
        }
        for vcf in vcf_results
    ], index=vcf_indices)
    
    # Assign all columns at once
    df_filtered[['chromosome', 'position', 'ref_allele', 'alt_allele']] = vcf_df
    
    # Fallback: For VCF conversion failures, try alternative methods
    vcf_failed_mask = df_filtered['chromosome'].isna()
    vcf_failed_count = vcf_failed_mask.sum()
    
    if vcf_failed_count > 0:
        print(f"\n{vcf_failed_count} variants failed VCF conversion. Attempting fallback methods...")
        
        # First, try SPDI conversion with anchor base fetching for those that have SPDI but failed
        has_spdi = df_filtered['Canonical SPDI'].notna()
        spdi_retry_mask = vcf_failed_mask & has_spdi
        spdi_retry_count = spdi_retry_mask.sum()
        
        if spdi_retry_count > 0:
            print(f"  Step 1: Re-trying {spdi_retry_count} variants with SPDI (may require anchor base fetch)...")
            # These might have failed due to network issues, try again
            # (Already tried in main loop, but worth one more attempt)
        
        # Second, try Mutalyzer normalization if cDNA is available
        has_cdna = df_filtered['hgvs_coding'].str.contains(':c.', na=False)
        can_retry = vcf_failed_mask & has_cdna
        retry_count = can_retry.sum()
        
        if retry_count > 0:
            print(f"  Step 2: {retry_count} variants have cDNA notation, attempting Mutalyzer normalization...")
            
            retry_indices = df_filtered[can_retry].index.tolist()
            mutalyzer_hgvs_dict = {}
            mutalyzer_vcf_dict = {}
            
            # Re-normalize through Mutalyzer and convert to VCF
            for idx in tqdm(retry_indices, desc="Mutalyzer fallback"):
                hgvs_c = df_filtered.loc[idx, 'hgvs_coding']
                
                # Parse cDNA notation
                parts = hgvs_c.split(':', 1)
                if len(parts) == 2:
                    transcript_acc = parts[0]
                    cdna_variant = parts[1]
                    
                    # Get Mutalyzer-normalized genomic HGVS
                    mutalyzer_hgvs_g = convert_cdna_to_genomic_hgvs_mutalyzer(
                        transcript_acc, 
                        cdna_variant, 
                        genomic_accession
                    )
                    
                    if mutalyzer_hgvs_g:
                        mutalyzer_hgvs_dict[idx] = mutalyzer_hgvs_g
                        
                        # Try VCF conversion with normalized HGVS
                        vcf = hgvs_g_to_vcf(mutalyzer_hgvs_g)
                        if vcf:
                            mutalyzer_vcf_dict[idx] = vcf
            
            # Update successful fallback conversions
            fallback_success = len(mutalyzer_vcf_dict)
            if fallback_success > 0:
                print(f"  Mutalyzer fallback succeeded for {fallback_success}/{retry_count} variants")
                
                # Update genomic HGVS with Mutalyzer-normalized versions
                for idx, hgvs_g in mutalyzer_hgvs_dict.items():
                    df_filtered.loc[idx, 'hgvs_genomic_38'] = hgvs_g
                
                # Update VCF fields with successful conversions
                for idx, vcf in mutalyzer_vcf_dict.items():
                    df_filtered.loc[idx, 'chromosome'] = vcf.get('chrom')
                    df_filtered.loc[idx, 'position'] = vcf.get('pos')
                    df_filtered.loc[idx, 'ref_allele'] = vcf.get('ref')
                    df_filtered.loc[idx, 'alt_allele'] = vcf.get('alt')
            else:
                print(f"  Mutalyzer fallback failed for all {retry_count} variants")
        else:
            print(f"  No cDNA notation available for Mutalyzer retry")
    
    # Convert chromosome and position to integer (after filtering out NaN values)
    # Use Int64 to handle any potential null values during intermediate steps
    df_filtered['chromosome'] = pd.to_numeric(df_filtered['chromosome'], errors='coerce')
    df_filtered['position'] = pd.to_numeric(df_filtered['position'], errors='coerce')
    
    # Add gene symbol
    df_filtered['gene_symbol'] = gene_symbol
    
    # Reorder columns to match required format
    output_columns = [
        'hgvs_genomic_38',
        'hgvs_coding',
        'chromosome',
        'position',
        'ref_allele',
        'alt_allele',
        'gene_symbol',
        'pathogenicity_original'
    ]
    
    df_output = df_filtered[output_columns].copy()
    
    # Identify and report VCF conversion failures
    vcf_failed_df = df_output[df_output['chromosome'].isna()].copy()
    if len(vcf_failed_df) > 0:
        print(f"\nFailed VCF conversions ({len(vcf_failed_df)} variants):")
        print("-" * 80)
        for idx, row in vcf_failed_df.iterrows():
            hgvs_g = row.get('hgvs_genomic_38', 'N/A')
            hgvs_c = row.get('hgvs_coding', 'N/A')
            print(f"  Genomic: {hgvs_g}")
            print(f"  cDNA:    {hgvs_c}")
            print()
    
    # Remove rows where VCF conversion failed
    df_output = df_output[df_output['chromosome'].notna()].copy()
    
    # Convert chromosome and position to integers (no NaN values at this point)
    df_output['chromosome'] = df_output['chromosome'].astype(int)
    df_output['position'] = df_output['position'].astype(int)
    
    print(f"\nFinal output rows (after VCF conversion): {len(df_output)}")
    print(f"\nSample output data:")
    print(df_output.head(10))
    
    # Save to CSV
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df_output.to_csv(output_file, index=False)
    print(f"\nSaved to: {output_file}")
    
    return df_output


if __name__ == "__main__":
    gene_symbol = "ATM"
    genomic_accession = "NC_000011.10"
    test_rows = 1000  # Set to 0 to process all rows
    input_file_path = f"../data_local/raw/clinvar/{gene_symbol}_clinvar_result.txt"
    output_file_path = f"../data_local/processed/clinvar/{gene_symbol}_variants.csv"
    
    # Batch processing settings
    batch_size = 100  # Process 100 variants per batch
    save_checkpoints = False  # Set to True to save intermediate results after each batch
    
    process_clinvar(
        input_file=input_file_path, 
        output_file=output_file_path, 
        gene_symbol=gene_symbol, 
        genomic_accession=genomic_accession, 
        test_rows=test_rows,
        batch_size=batch_size,
        save_checkpoints=save_checkpoints
    )
