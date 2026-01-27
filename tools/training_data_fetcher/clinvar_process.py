import re
import pandas as pd
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
import os
import sys
import requests
import time

# Add the parent directory to the Python path to enable package imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import convert_cdna_to_genomic_hgvs_mutalyzer from hgvs_c_to_g module
from tools.variant_processor.hgvs_c_to_g import convert_cdna_to_genomic_hgvs_mutalyzer

# Legacy mapping for compatibility
PATHOGENICITY_STANDARD = {
    'pathogenic': 'pathogenic',
    'likely pathogenic': 'likely_pathogenic',
    'pathogenic/likely pathogenic': 'pathogenic_or_likely',


    'benign': 'benign',
    'likely benign': 'likely_benign',
    'benign/likely benign': 'benign_or_likely',

    'uncertain significance': 'unknown',
    'not yet reviewed': 'unknown',
    'not provided': 'unknown',

    'conflicting interpretations of pathogenicity': 'conflicting_interpretations',
}

def extract_hgvs_protein(name_field: str) -> Optional[str]:
    """
    Extract HGVS protein notation from ClinVar Name field.
    
    Args:
        name_field: ClinVar Name field (e.g., "NM_000138.5(FBN1):c.1011C>A (p.Tyr337Ter)")
        
    Returns:
        HGVS protein notation (e.g., "p.Tyr337Ter")
    """
    if not name_field or pd.isna(name_field):
        return None
        
    # Extract protein change from parentheses
    match = re.search(r'\(p\.([^)]+)\)', name_field)
    if match:
        return f"p.{match.group(1)}"
    
    return None

def extract_hgvs_coding(name_field: str) -> Optional[str]:
    """
    Extract HGVS coding notation from ClinVar Name field.
    
    Args:
        name_field: ClinVar Name field (e.g., "NM_000138.5(FBN1):c.*730G>T")
        
    Returns:
        HGVS coding notation without gene and protein info (e.g., "NM_000138.5:c.*730G>T")
    """
    if not name_field or pd.isna(name_field):
        return None
        
    # Extract the transcript and coding part, remove gene and protein info
    # Pattern: NM_000138.5(FBN1):c.*730G>T (p.Something) -> NM_000138.5:c.*730G>T
    match = re.search(r'(NM_\d+\.\d+)\([^)]+\):(c\.[^)]*?)(?:\s*\([^)]*\))?$', name_field)
    if match:
        transcript, coding = match.groups()
        return f"{transcript}:{coding.strip()}"
    
    return None

class ClinVarProcessor:
    """
    Simplified ClinVar processor for creating variant DataFrames.
    """
    
    def __init__(self, input_file_path: str, logger=None):
        """Initialize the ClinVarProcessor."""
        self.logger = logger or self._setup_logger()
        self.df_clinvar = self._read_clinvar_tsv(input_file_path)
    
    def _setup_logger(self):
        """Set up default logger for the processor."""
        logger = logging.getLogger(f"{__name__}.ClinVarProcessor")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG)
        return logger
    
    def _read_clinvar_tsv(self, input_file_path: str) -> Optional[pd.DataFrame]:
        """
        Read ClinVar TSV file and return as DataFrame.
        
        Args:
            tsv_filepath: Path to the ClinVar TSV file
            
        Returns:
            pandas.DataFrame: DataFrame containing the ClinVar data, or None if error
        """
        self.logger.info(f"Reading ClinVar TSV file: {input_file_path}")
        
        try:
            df = pd.read_csv(input_file_path, sep='\t', encoding='utf-8')
            self.logger.info(f"Successfully loaded {len(df)} variants from ClinVar TSV")
            return df
        except FileNotFoundError:
            self.logger.error(f"TSV file not found at {input_file_path}")
            return None
        except Exception as e:
            self.logger.error(f"An error occurred while reading the TSV file: {e}")
            return None
    
    def _get_gene_symbol(self) -> Optional[str]:
        """
        Get the gene symbol from the ClinVar DataFrame.
        
        Args:
            df: DataFrame containing variant data
        
        Returns:
            Optional[str]: Gene symbol if found, otherwise None
        """
        if self.df_clinvar is None or self.df_clinvar.empty:
            return None
        
        # Check for various gene symbol column names
        gene_columns = ['Gene(s)', 'Gene symbol', 'Entrez Gene', 'Gene']
        
        for col_name in gene_columns:
            if col_name in self.df_clinvar.columns:
                # Get unique gene symbols, filter out empty/null values
                gene_symbols = self.df_clinvar[col_name].dropna().unique().tolist()
                if gene_symbols:
                    # Return the first non-empty gene symbol
                    for symbol in gene_symbols:
                        if str(symbol).strip():
                            return str(symbol).strip()
                
        return None
    
    def get_variant_stats(self) -> Dict[str, Any]:
        """
        Generate statistics for ClinVar variants.
        
        Args:
            df: DataFrame containing variant data
            
        Returns:
            dict: Statistics dictionary
        """
        if self.df_clinvar is None or self.df_clinvar.empty:
            return {}
        
        stats = {
            'total_variants': int(len(self.df_clinvar)),
            'pathogenicity_distribution': {},
            'variant_types': {},
            'molecular_consequences': {}
        }
        
        # Count pathogenicity classifications
        if 'Germline classification' in self.df_clinvar.columns:
            pathogenicity_counts = self.df_clinvar['Germline classification'].value_counts().to_dict()
            stats['pathogenicity_distribution'] = {k: int(v) for k, v in pathogenicity_counts.items()}
        
        # Count variant types
        if 'Variant type' in self.df_clinvar.columns:
            variant_type_counts = self.df_clinvar['Variant type'].value_counts().to_dict()
            stats['variant_types'] = {k: int(v) for k, v in variant_type_counts.items()}
        
        # Count molecular consequences
        if 'Molecular consequence' in self.df_clinvar.columns:
            consequence_counts = self.df_clinvar['Molecular consequence'].value_counts().to_dict()
            stats['molecular_consequences'] = {k: int(v) for k, v in consequence_counts.items()}
        
        return stats
    
    def parse_spdi_to_variant_components(self, spdi_notation: str) -> Tuple[Optional[str], Optional[int], Optional[str], Optional[str]]:
        """
        Parse SPDI notation to extract chromosome, position, ref, and alt alleles.
        
        Note: SPDI insertions don't include anchor bases by design. For proper VCF representation
        of insertions, use hgvs_coding with an API converter (e.g., Mutalyzer).
        
        Args:
            spdi_notation: SPDI notation string (e.g., "NC_000015.10:48645780:G:A")
            
        Returns:
            tuple: (chromosome, position, ref_allele, alt_allele) or (None, None, None, None)
        """
        if not isinstance(spdi_notation, str) or not spdi_notation.strip():
            return None, None, None, None
            
        # Regex to parse SPDI: Sequence:Position:Deletion:Insertion
        # Note: Accepts empty deletion/insertion (for insertions/deletions without anchor base)
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
                # Substitution or complex variant (delins)
                ref_allele = deletion
                alt_allele = insertion
            elif deletion and not insertion:
                # Deletion
                ref_allele = deletion
                alt_allele = ""
            elif not deletion and insertion:
                # Insertion (without anchor base - SPDI limitation)
                # For proper VCF, this needs reference genome lookup or hgvs_coding conversion
                ref_allele = ""
                alt_allele = insertion
            else:
                # No change (shouldn't happen in practice)
                ref_allele = ""
                alt_allele = ""
            
            return chromosome, position, ref_allele, alt_allele
        else:
            return None, None, None, None
    
    def parse_spdi_to_genomic_hgvs_grch38(self, spdi_notation: str) -> Optional[str]:
        """
        Converts SPDI notation to GRCh38 genomic HGVS (g. format).
        Handles substitutions, insertions, deletions, and complex indels.
        
        Args:
            spdi_notation: SPDI notation string (e.g., "NC_000011.10:108227650:T:CC")
            
        Returns:
            str: Genomic HGVS notation, or None if conversion not possible
        """
        # Regex to parse SPDI: Sequence:Position:Deletion:Insertion
        # Handle variable length deletions and insertions
        match = re.match(r"^(NC_\d+\.\d+):(\d+):([ACGT]*):([ACGT]*)$", spdi_notation)

        if match:
            sequence, pos_0based_str, deletion, insertion = match.groups()
            pos_0based = int(pos_0based_str)
            
            # Convert to 1-based position for HGVS
            pos_1based = pos_0based + 1

            # Case 1: Simple substitution (both 1 base)
            if len(deletion) == 1 and len(insertion) == 1:
                genomic_hgvs = f"{sequence}:g.{pos_1based}{deletion}>{insertion}"
                return genomic_hgvs
            
            # Case 2: Insertion (no deletion, only insertion)
            elif len(deletion) == 0 and len(insertion) > 0:
                # Insertion notation: pos_pos+1insSequence
                pos_after = pos_1based + 1
                genomic_hgvs = f"{sequence}:g.{pos_1based}_{pos_after}ins{insertion}"
                return genomic_hgvs
            
            # Case 3: Deletion (deletion only, no insertion)
            elif len(deletion) > 0 and len(insertion) == 0:
                # Deletion notation: pos_endposdel or posdel (for 1 base)
                if len(deletion) == 1:
                    genomic_hgvs = f"{sequence}:g.{pos_1based}del"
                else:
                    end_pos = pos_1based + len(deletion) - 1
                    genomic_hgvs = f"{sequence}:g.{pos_1based}_{end_pos}del"
                return genomic_hgvs
            
            # Case 4: Complex indel/delins (both deletion and insertion)
            elif len(deletion) > 0 and len(insertion) > 0:
                # DelIns notation: pos_endposdelinsSequence
                if len(deletion) == 1:
                    # Single base replaced with multiple bases
                    genomic_hgvs = f"{sequence}:g.{pos_1based}delins{insertion}"
                else:
                    # Multiple bases replaced
                    end_pos = pos_1based + len(deletion) - 1
                    genomic_hgvs = f"{sequence}:g.{pos_1based}_{end_pos}delins{insertion}"
                return genomic_hgvs
            
            # Case 5: Empty SPDI (shouldn't happen)
            else:
                return None
        else:
            return None
        
    def _create_variants_dataframe(self) -> pd.DataFrame:
        """
        Create a simplified variants DataFrame following the VariantModel schema.
        
        Args:
            df: ClinVar DataFrame
            
        Returns:
            DataFrame with variant data following VariantModel schema
        """
        if self.df_clinvar is None or self.df_clinvar.empty:
            self.logger.warning("Empty DataFrame provided for variant processing")
            return pd.DataFrame()
        
        # Extract gene symbol from the DataFrame
        gene_symbol = self._get_gene_symbol()
        if not gene_symbol:
            self.logger.error("Could not extract gene symbol from ClinVar data")
            return pd.DataFrame()
        
        self.logger.info(f"Creating variants DataFrame for {len(self.df_clinvar)} ClinVar variants for gene {gene_symbol}")
        
        variants_data = []
        
        for idx, row in self.df_clinvar.iterrows():
            try:
                # Extract chromosome, position, ref, alt from SPDI
                spdi_notation = str(row.get('Canonical SPDI', ''))
                if pd.notna(spdi_notation) and spdi_notation:
                    chromosome, position, ref_allele, alt_allele = self.parse_spdi_to_variant_components(spdi_notation)
                else:
                    chromosome, position, ref_allele, alt_allele = None, None, None, None
                
                # Extract HGVS information from Name field
                name_field = row.get('Name', '')
                hgvs_coding = extract_hgvs_coding(name_field)
                hgvs_protein = extract_hgvs_protein(name_field)
                
                # Use SPDI notation to get genomic HGVS
                hgvs_genomic_38 = self.parse_spdi_to_genomic_hgvs_grch38(spdi_notation) if spdi_notation else None
                
                # Fallback: If SPDI parsing failed, try Mutalyzer API with hgvs_coding
                if not hgvs_genomic_38 and hgvs_coding:
                    # Extract transcript and try to get genomic reference
                    transcript_match = re.match(r'(NM_\d+\.\d+)', str(hgvs_coding))
                    if transcript_match and spdi_notation:
                        # Try to extract genomic accession from SPDI
                        spdi_parts = spdi_notation.split(':')
                        if len(spdi_parts) >= 1:
                            genomic_acc = spdi_parts[0]  # e.g., NC_000016.10
                            transcript_acc = transcript_match.group(1)
                            
                            # Extract c. part
                            if ':c.' in hgvs_coding:
                                cdna_part = 'c.' + hgvs_coding.split(':c.')[1]
                            else:
                                cdna_part = hgvs_coding
                            
                            # Try Mutalyzer API
                            hgvs_genomic_38 = convert_cdna_to_genomic_hgvs_mutalyzer(
                                transcript_acc, 
                                cdna_part, 
                                genomic_acc
                            )
                            
                            if hgvs_genomic_38:
                                self.logger.debug(f"Recovered variant {idx} via Mutalyzer: {hgvs_genomic_38}")
                            else:
                                self.logger.debug(f"Variant {idx}: Mutalyzer API failed. cDNA: {hgvs_coding}, "
                                               f"Transcript: {transcript_acc}, Genomic: {genomic_acc}")
                
                # Skip if we still don't have genomic HGVS or basic components
                if not hgvs_genomic_38:
                    self.logger.debug(f"Skipping variant at index {idx}: could not get genomic HGVS. "
                                    f"cDNA: {hgvs_coding}, SPDI: {spdi_notation[:100] if spdi_notation else 'None'}")
                    continue
                
                # If SPDI parsing failed but we got genomic HGVS from API, re-parse components
                if not all([chromosome, position, ref_allele is not None, alt_allele is not None]):
                    # Try to extract from hgvs_coding as fallback
                    if hgvs_coding:
                        try_ref, try_alt = None, None
                        # Try substitution: e.g., "c.1011C>A"
                        if ':c.' in hgvs_coding:
                            coding_part = hgvs_coding.split(':c.')[1]
                        else:
                            coding_part = hgvs_coding.lstrip('c.')
                        
                        sub_match = re.match(r'(\d+)([ACGT])>([ACGT])', coding_part)
                        if sub_match:
                            pos, try_ref, try_alt = sub_match.groups()
                            ref_allele = try_ref
                            alt_allele = try_alt
                        else:
                            # hgvs_coding exists but doesn't have extractable base alleles
                            # (e.g., insertions like "c.3247_3248insT" or "c.*6_*13delins...")
                            if not try_ref and not try_alt:
                                self.logger.debug(f"Variant {idx}: hgvs_coding without base allele. "
                                               f"cDNA: {hgvs_coding} (insertion/deletion/complex)")
                    
                    # Extract chromosome and position from hgvs_genomic_38 if possible
                    if not chromosome or not position:
                        # Try to extract from genomic HGVS: NC_000016.10:g.23603462T>C
                        g_match = re.match(r'(NC_\d+\.\d+):g.(\d+)', hgvs_genomic_38)
                        if g_match:
                            genomic_acc = g_match.group(1)
                            pos_str = g_match.group(2)
                            # Extract chromosome from accession
                            chrom_match = re.match(r'NC_0*(\d+)\.\d+', genomic_acc)
                            if chrom_match:
                                chromosome = chrom_match.group(1)
                                position = int(pos_str)
                    
                    # Final check: skip if still missing critical data
                    if not all([chromosome, position, alt_allele]):
                        self.logger.debug(f"Skipping variant at index {idx}: missing critical components after recovery")
                        continue
                
                # Process pathogenicity
                germline_classification = str(row.get('Germline classification', ''))
                
                # First standardize using PATHOGENICITY_STANDARD
                pathogenicity_original = PATHOGENICITY_STANDARD.get(
                    germline_classification.lower().strip(), 
                    germline_classification
                )
                
                # Convert data types: chromosome and position to int, ref_allele and alt_allele to str
                try:
                    chromosome = int(chromosome)
                    position = int(position)
                    ref_allele = str(ref_allele).strip()
                    alt_allele = str(alt_allele).strip()
                except (ValueError, TypeError) as e:
                    self.logger.debug(f"Skipping variant at index {idx}: type conversion error - {e}")
                    continue
                
                # Keep empty ref_allele if present (e.g., insertions from SPDI without anchor base)
                # Just proceed with the data as is
                if not ref_allele and not alt_allele:
                    self.logger.debug(f"Skipping variant at index {idx}: both ref_allele and alt_allele are empty")
                    continue

                # Create variant record
                variant_record = {
                    'hgvs_genomic_38': hgvs_genomic_38,
                    'hgvs_coding': hgvs_coding,
                    'hgvs_protein': hgvs_protein,
                    'chromosome': chromosome,
                    'position': position,
                    'ref_allele': ref_allele,
                    'alt_allele': alt_allele,
                    'gene_symbol': gene_symbol,
                    'pathogenicity_original': pathogenicity_original,
                }
                
                variants_data.append(variant_record)
                
            except Exception as e:
                self.logger.error(f"Error processing variant at index {idx}: {e}")
                continue
        
        if variants_data:
            result_df = pd.DataFrame(variants_data)
            self.logger.info(f"Successfully created DataFrame with {len(result_df)} variants")
            return result_df
        else:
            self.logger.warning("No variants could be processed")
            return pd.DataFrame()
    
    def get_processed_variants_dataframe(self) -> dict:
        """
        Get the processed variants DataFrame.
        """
        return {
            'gene_symbol': self._get_gene_symbol(),
            'df': self._create_variants_dataframe(),
            'df_stats': self.get_variant_stats()
        }

def main():
    """
    Main function to process ClinVar data.
    """
    input_file_path = "data_local_raw/clinvar_raw/palb2_clinvar_result.txt"
    clinvar_processor = ClinVarProcessor(input_file_path)
    processed_variants_dataframe = clinvar_processor.get_processed_variants_dataframe()
    print(processed_variants_dataframe['df'].head())
    processed_variants_dataframe['df'].to_csv("ATM_variants.csv", index=False)

if __name__ == "__main__":
    main()
