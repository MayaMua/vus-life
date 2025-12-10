import streamlit as st
from typing import Dict, Any
import os
from pathlib import Path

def create_sidebar() -> Dict[str, Any]:
    """
    Create and configure the sidebar with all configuration and display options.
    
    Returns:
        Dict[str, Any]: Dictionary containing all selected configuration values
    """
    with st.sidebar:
        st.title("🧬 VUS Life")
        
        # Configuration Section
        st.header("⚙️ Configuration")
        
        # Select Gene dropdown
        gene_options = ["BRCA1", "BRCA2", "FBN1"]
        selected_gene = st.selectbox(
            "Select Gene:",
            options=gene_options,
            index=0,  # Default to BRCA1
            key="gene_selection"
        )
        
        # Select Annotation Type dropdown
        annotation_options = ["vep", "clinvar", "gnomad"]
        selected_annotation = st.selectbox(
            "Select Annotation Type:",
            options=annotation_options,
            index=0,  # Default to vep
            key="annotation_selection"
        )
        
        # Select Model dropdown
        model_options = ["all-mpnet-base-v2", "all-MiniLM-L6-v2", "paraphrase-multilingual-MiniLM-L12-v2"]
        selected_model = st.selectbox(
            "Select Model:",
            options=model_options,
            index=0,  # Default to all-mpnet-base-v2
            key="model_selection"
        )
        
        st.divider()
        
        # Display Options Section
        st.header("📊 Display Options")
        
        # Color by dropdown
        color_options = ["Binary Classification", "Pathogenicity Score", "Clinical Significance", "Population Frequency"]
        selected_color = st.selectbox(
            "Color by:",
            options=color_options,
            index=0,  # Default to Binary Classification
            key="color_selection"
        )
        
        st.divider()
        
        # Variant Input Section
        st.header("🧬 Variant Input")
        
        # Variant input text area
        variant_input = st.text_area(
            "Enter variants (one per line):",
            height=150,
            placeholder="Enter variant IDs, HGVS notations, or genomic coordinates...\nExample:\nBRCA1:c.5266dupG\nBRCA2:p.Arg1443Ter\n17:41276045:G>A",
            key="variant_input",
            help="Enter variants for the selected gene. Each variant should be on a separate line."
        )
        
        # Variant file management
        st.subheader("📁 Variant File Management")
        
        # Get the variants file path
        variants_file_path = get_variants_file_path(selected_gene)
        
        # Display current file status
        if variants_file_path.exists():
            file_size = variants_file_path.stat().st_size
            st.success(f"✅ Variants file exists ({file_size} bytes)")
            
            # Show current content preview
            with st.expander("📖 View current variants file"):
                try:
                    with open(variants_file_path, 'r') as f:
                        content = f.read()
                        if content.strip():
                            st.text_area("Current variants:", content, height=100, disabled=True)
                        else:
                            st.info("File is empty")
                except Exception as e:
                    st.error(f"Error reading file: {e}")
        else:
            st.info("📄 No variants file found for this gene")
        
        # Update button
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Update Variants File", type="primary"):
                if variant_input.strip():
                    try:
                        # Create directory if it doesn't exist
                        variants_file_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Write variants to file
                        with open(variants_file_path, 'w') as f:
                            f.write(variant_input.strip())
                        
                        st.success(f"✅ Updated variants file for {selected_gene}")
                        st.rerun()  # Refresh the page to show updated content
                        
                    except Exception as e:
                        st.error(f"❌ Error updating file: {e}")
                else:
                    st.warning("⚠️ Please enter some variants before updating the file")
        
        with col2:
            if st.button("🗑️ Clear File"):
                try:
                    if variants_file_path.exists():
                        variants_file_path.unlink()
                        st.success(f"✅ Cleared variants file for {selected_gene}")
                        st.rerun()  # Refresh the page
                    else:
                        st.info("📄 No file to clear")
                except Exception as e:
                    st.error(f"❌ Error clearing file: {e}")
        
        # Load existing variants into input box if file exists
        if variants_file_path.exists() and not variant_input.strip():
            try:
                with open(variants_file_path, 'r') as f:
                    existing_content = f.read()
                    if existing_content.strip():
                        # Update the text area with existing content
                        st.session_state.variant_input = existing_content
            except Exception as e:
                st.warning(f"Could not load existing variants: {e}")
        
        st.divider()
        
        # Cache Management Section
        st.header("⚡ Cache Management")
        st.write("Clear caches to force recomputation of embeddings and dimension reduction.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear Embedding Cache"):
                # Clear Streamlit cache
                st.cache_data.clear()
                st.success("✅ Embedding cache cleared")
                st.rerun()
        
        with col2:
            if st.button("🗑️ Clear All Caches"):
                # Clear Streamlit cache and session state
                st.cache_data.clear()
                if 'dimension_reduction_cache' in st.session_state:
                    del st.session_state.dimension_reduction_cache
                st.success("✅ All caches cleared")
                st.rerun()
    
    # Return all selected configurations
    return {
        "gene": selected_gene,
        "annotation_type": selected_annotation,
        "model": selected_model,
        "color_by": selected_color,
        "variant_input": variant_input
    }

def get_variants_file_path(gene: str) -> Path:
    """
    Get the path to the variants file for a specific gene.
    
    Args:
        gene: Gene symbol (e.g., 'BRCA1', 'BRCA2')
        
    Returns:
        Path to the variants file
    """
    # Create a variants directory in the project root
    project_root = Path(__file__).parent.parent
    variants_dir = project_root / "user_variants"
    variants_file = variants_dir / f"{gene}_variants.txt"
    return variants_file

def get_available_genes() -> list:
    """
    Get list of available genes for selection.
    
    Returns:
        list: List of available gene names
    """
    return ["BRCA1", "BRCA2", "FBN1", "TP53", "MYH7"]

def get_available_annotations() -> list:
    """
    Get list of available annotation types.
    
    Returns:
        list: List of available annotation types
    """
    return ["vep", "clinvar", "gnomad"]

def get_available_models() -> list:
    """
    Get list of available embedding models.
    
    Returns:
        list: List of available model names
    """
    return ["all-mpnet-base-v2", "all-MiniLM-L6-v2", "paraphrase-multilingual-MiniLM-L12-v2"]

def get_color_options() -> list:
    """
    Get list of available color options for visualization.
    
    Returns:
        list: List of available color options
    """
    return ["Binary Classification", "Pathogenicity Score", "Clinical Significance", "Population Frequency"]

def display_configuration_summary(config: Dict[str, Any]) -> None:
    """
    Display a summary of the current configuration in the main area.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary from create_sidebar()
    """
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Current Configuration")
        st.write(f"**Gene:** {config['gene']}")
        st.write(f"**Annotation Type:** {config['annotation_type']}")
        st.write(f"**Model:** {config['model']}")
    
    with col2:
        st.subheader("Display Settings")
        st.write(f"**Color by:** {config['color_by']}")
    
    # Display variant input summary
    if config.get('variant_input', '').strip():
        st.subheader("🧬 Variant Input Summary")
        variant_lines = [line.strip() for line in config['variant_input'].split('\n') if line.strip()]
        st.write(f"**Number of variants entered:** {len(variant_lines)}")
        
        # Show first few variants as preview
        if len(variant_lines) <= 5:
            st.write("**Variants:**")
            for i, variant in enumerate(variant_lines, 1):
                st.write(f"{i}. {variant}")
        else:
            st.write("**First 5 variants:**")
            for i, variant in enumerate(variant_lines[:5], 1):
                st.write(f"{i}. {variant}")
            st.write(f"... and {len(variant_lines) - 5} more variants")
        
        # Show file status
        variants_file_path = get_variants_file_path(config['gene'])
        if variants_file_path.exists():
            st.success(f"✅ Variants file exists for {config['gene']}")
        else:
            st.info(f"📄 Click 'Update Variants File' to save these variants for {config['gene']}")
    else:
        st.subheader("🧬 Variant Input Summary")
        st.info("No variants entered. Use the sidebar to enter variants for analysis.")
