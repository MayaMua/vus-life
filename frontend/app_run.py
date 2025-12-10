
import streamlit as st
import sys
import os
from pathlib import Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sidebar_config import create_sidebar, display_configuration_summary
from database_stats import main as database_stats_main


def main():
    st.set_page_config(
        page_title="VUS Life - Variant Analysis",
        page_icon="🧬",
        layout="wide"
    )
    
    
    # Get project root directory
    project_root = Path(__file__).parent.parent
    
    # Create sidebar and get configuration
    config = create_sidebar()
    
    # Main content area
    st.title("🧬 VUS Life - Variant Analysis Dashboard")
    st.write("Welcome to the VUS Life variant analysis platform! Explore dimension reduction results and database statistics for genomic variants.")
    
    # Add page selection
    page = st.sidebar.selectbox(
        "Select Page:",
        ["Dimension Reduction Analysis", "Variant Prediction", "Database Statistics"],
        index=0
    )
    
    if page == "Dimension Reduction Analysis":
        # Display configuration summary
        display_configuration_summary(config)
        
        # Display dimension reduction results
        st.divider()
        display_dimension_reduction_results(
            gene=config['gene'],
            annotation_type=config['annotation_type'],
            model=config['model'],
        )
    elif page == "Variant Prediction":
        # Display configuration summary
        display_configuration_summary(config)
        
        # Parse variant input
        variant_input = config.get('variant_input', '').strip()
        
        if variant_input:
            # Parse variants from input
            hgvs_list = [line.strip() for line in variant_input.split('\n') if line.strip()]
            
            # Add manual trigger button
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("🚀 Run Prediction", type="primary"):
                    st.rerun()
            
            # Display prediction results
            st.divider()
            display_variant_prediction_results(
                gene=config['gene'],
                model=config['model'],
                hgvs_list=hgvs_list,
                project_root=project_root
            )
        else:
            st.info("Please enter variants in the sidebar to run predictions.")
            st.write("**Instructions:**")
            st.write("1. Enter HGVS variants in the text area in the sidebar")
            st.write("2. Click 'Update Variants File' to save the variants")
            st.write("3. The prediction results will appear here automatically")
    elif page == "Database Statistics":
        # Display database statistics
        st.divider()
        database_stats_main()

if __name__ == "__main__":
    main()
