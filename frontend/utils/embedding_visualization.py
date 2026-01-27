import matplotlib.pyplot as plt
import numpy as np
from sklearn.preprocessing import LabelEncoder
from matplotlib.colors import ListedColormap
import os
from matplotlib.lines import Line2D
from typing import List, Dict, Any, Optional, Tuple, Union, Literal
import logging
import pandas as pd
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Standard colors for binary classification (benign: blue, pathogenic: red)
BINARY_COLORS = {'benign': '#5555FF', 'pathogenic': '#FF5555'}
# FOUR_CLASS_COLORS = {'benign': '#5094D5', 'likely_benign': '#ABD8E5', 'likely_pathogenic': '#F9AD95', 'pathogenic': '#D15354'}

# Comprehensive color mapping for all pathogenicity categories used across different genes
COMPREHENSIVE_PATHOGENICITY_COLORS = {
    # BRCA categories (5 types)
    'pathogenic': '#FF5555',           # Red
    'likely_pathogenic': '#D15354',    # Yellow

    'benign': '#5094D5',              # Blue
    'likely_benign': '#5555FF',       # Light blue
    'not_yet_reviewed': '#00FF00',    # Green
    
    # Additional categories (ClinVar combined categories)
    'pathogenic_or_likely': '#F9AD95',     # Dark red (between pathogenic and likely_pathogenic)
    'benign_or_likely': '#ABD8E5',         # Dark blue (between benign and likely_benign)
    
    # Uncertain significance (if present)
    'uncertain_significance': '#00FF00',    # 
    'unknown': '#00FF00',                   # Dark green for unknown variants
    'query': '#00FF00'                      # Dark red for test variants (query)
}

def format_gene_name_in_title(fig: plt.Figure, title: str, gene_symbol: Optional[str] = None, 
                              y_pos: float = 0.98, fontsize: int = 28) -> None:
    """
    Draw title with gene name formatted as bold italic using direct text positioning.
    Calculates positions for each word segment and draws them separately.
    
    Args:
        fig: Matplotlib figure object to draw on
        title: The title string that may contain a gene symbol
        gene_symbol: Optional gene symbol to format. If None, tries to extract from title.
        y_pos: Y position for the title (default 0.98, near top)
        fontsize: Font size for the title (default 28)
    """
    if not gene_symbol:
        # Try to extract common gene patterns (uppercase letters and numbers)
        # Pattern for gene symbols (typically 2-10 uppercase letters/numbers)
        gene_pattern = r'\b([A-Z][A-Z0-9]{1,9})\b'
        matches = re.findall(gene_pattern, title)
        if matches:
            # Use the first match (likely the gene symbol)
            gene_symbol = matches[0]
    
    if gene_symbol:
        # Split title into parts: prefix, gene name, suffix
        pattern = re.compile(re.escape(gene_symbol), re.IGNORECASE)
        match = pattern.search(title)
        if match:
            prefix = title[:match.start()].strip()
            gene_name = match.group()
            suffix = title[match.end():].strip()
            
            # Use approximate character width for positioning (rough estimate)
            # Average character width in points for fontsize 28 is approximately 0.01-0.015 of figure width
            char_width = 0.012  # Approximate width per character as fraction of figure width
            
            # Add extra spacing between prefix and gene name (only if prefix exists)
            spacing_before = 0.015 if prefix else 0.0  # Additional space between prefix and gene name
            # Add extra spacing between gene name and suffix (only if suffix exists)
            spacing_after = 0.025 if suffix else 0.0  # Additional space between gene name and suffix (increased for hyphen)
            
            prefix_width = len(prefix) * char_width if prefix else 0
            gene_width = len(gene_name) * char_width * 0.9  # Italic text slightly narrower
            suffix_width = len(suffix) * char_width if suffix else 0
            
            total_width = prefix_width + spacing_before + gene_width + spacing_after + suffix_width
            start_x = 0.5 - total_width / 2
            
            # Create text elements with calculated positions
            current_x = start_x
            if prefix:
                fig.text(current_x + prefix_width / 2, y_pos, prefix, fontsize=fontsize, fontweight='bold',
                        ha='center', va='top', transform=fig.transFigure)
                current_x += prefix_width + spacing_before
            
            fig.text(current_x + gene_width / 2, y_pos, gene_name, 
                    fontsize=fontsize, fontweight='bold', style='italic', ha='center', va='top', 
                    transform=fig.transFigure)
            current_x += gene_width + spacing_after
            
            if suffix:
                fig.text(current_x + suffix_width / 2, y_pos, suffix, 
                        fontsize=fontsize, fontweight='bold', ha='center', va='top', transform=fig.transFigure)
        else:
            # Gene symbol not found in title, just draw the whole title
            fig.text(0.5, y_pos, title, fontsize=fontsize, fontweight='bold',
                    ha='center', va='top', transform=fig.transFigure)
    else:
        # No gene symbol, just draw the whole title
        fig.text(0.5, y_pos, title, fontsize=fontsize, fontweight='bold',
                ha='center', va='top', transform=fig.transFigure)

def create_combined_embedding_figure(merged_df: pd.DataFrame, 
                                    figure_title: str,
                                    model_name: Optional[str] = None,
                                    gene_symbol: Optional[str] = None,
                                    figsize: Tuple[int, int] = (18, 8), 
                                    save_path: Optional[str] = None, 
                                    show: bool = False) -> plt.Figure:
    """
    Create a combined figure showing embedding results for 3 dimension reduction methods.
    
    Args:
        merged_df: DataFrame with columns: variant_id, pca_x, pca_y, tsne_x, tsne_y, umap_x, umap_y, labels
        figure_title: Title for the figure
        model_name: Name of the embedding model to display on the left side (optional)
        gene_symbol: Gene symbol to format as bold italic in the title (optional)
        figsize: Figure size (width, height)
        save_path: Path to save the combined plot
        show: Whether to display the plot
        
    Returns:
        Matplotlib figure object
    """
    # Check that required 'labels' column exists
    if 'labels' not in merged_df.columns:
        raise ValueError("DataFrame must have a column named 'labels'")
    
    methods = ['PCA', 't-SNE', 'UMAP']  # Standard order for titles
    method_columns = ['pca', 't-sne', 'umap']  # Column names in your data (with hyphen for t-sne)
    
    # Create figure with subplots (1 row, 3 columns)
    fig, axes = plt.subplots(1, 3, figsize=figsize)
    
    # Use comprehensive color map
    color_map = COMPREHENSIVE_PATHOGENICITY_COLORS
    
    # Debug: Print available columns
    print(f"Available columns: {list(merged_df.columns)}")
    
    # Get unique labels for legend
    unique_labels = sorted(merged_df['labels'].unique()) 
    print(f"Unique labels: {unique_labels}")
    
    # Create legend elements with special handling for test variants
    legend_elements = []
    for i, label in enumerate(unique_labels):
        color = color_map.get(label, "#888888")
        
        # Special styling for test variants (query/unknown)
        if label in ['query', 'unknown', 'not_yet_reviewed']:
            legend_elements.append(Line2D([0], [0], marker='D', color='w',
                                         markerfacecolor=color, markersize=10,
                                         markeredgecolor='black', markeredgewidth=1.0,
                                         label=f'{label} (unknown)', alpha=0.9))
        else:
            legend_elements.append(Line2D([0], [0], marker='o', color='w',
                                         markerfacecolor=color, markersize=12, 
                                         label=f'{label} (known)', alpha=0.7))
    
    # Plot each method
    for i, (method_title, method_col) in enumerate(zip(methods, method_columns)):
        ax = axes[i]
        
        # Get coordinates for this method
        x_col = f"{method_col}_x"
        y_col = f"{method_col}_y"
        
        print(f"Looking for columns: {x_col}, {y_col}")
        
        if x_col in merged_df.columns and y_col in merged_df.columns:
            # Filter out NaN values
            valid_mask = merged_df[x_col].notna() & merged_df[y_col].notna()
            
            # Debug: Print counts for each label
            if i == 0:  # Only print for first method
                print(f"\nDebug info for {method_title}:")
                for label in unique_labels:
                    total_count = (merged_df['labels'] == label).sum()
                    valid_count = ((merged_df['labels'] == label) & valid_mask).sum()
                    print(f"  {label}: {valid_count}/{total_count} variants with valid coordinates")
            
            if valid_mask.any():
                # Plot each class
                for label in unique_labels:
                    mask = (merged_df['labels'] == label) & valid_mask
                    if mask.any():
                        color = color_map.get(label, "#888888")
                        
                        # Special styling for test variants (query/unknown)
                        if label in ['query', 'unknown', 'not_yet_reviewed']:
                            # Use diamond markers with black edge for test variants
                            ax.scatter(merged_df.loc[mask, x_col], merged_df.loc[mask, y_col], 
                                      c=color, alpha=0.9, s=50, marker='D', 
                                      edgecolors='black', linewidths=1.0)
                        else:
                            # Use circle markers for training variants (increased size for visibility)
                            ax.scatter(merged_df.loc[mask, x_col], merged_df.loc[mask, y_col], 
                                      c=color, alpha=0.8, s=25, marker='o', edgecolors='none')
                
                # Set labels and grid
                ax.set_xlabel('Component 1', fontsize=14)
                ax.set_ylabel('Component 2', fontsize=14)
                ax.grid(True, alpha=0.3)
                ax.set_title(f'{method_title}', fontsize=18, fontweight='bold', pad=20)
            else:
                # Handle case with no valid data
                ax.text(0.5, 0.5, f'{method_title}\nNo valid data', ha='center', va='center',
                       transform=ax.transAxes, fontsize=14, color='gray')
                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_title(f'{method_title}', fontsize=18, fontweight='bold', pad=20)
        else:
            # Handle missing columns
            ax.text(0.5, 0.5, f'{method_title}\nMissing columns', ha='center', va='center',
                   transform=ax.transAxes, fontsize=14, color='gray')
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title(f'{method_title}', fontsize=18, fontweight='bold', pad=20)
    
    # Set main title with gene name formatted as bold italic
    format_gene_name_in_title(fig, figure_title, gene_symbol, y_pos=0.98, fontsize=24)
    
    # Add model name on the left side of the figure (vertical text)
    if model_name:
        # Position the text on the left side, vertically centered
        fig.text(0.02, 0.5, model_name, fontsize=20, fontweight='bold',
                rotation=90, ha='center', va='center', 
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Add legend at the bottom
    fig.legend(handles=legend_elements, loc='lower center', ncol=len(legend_elements), 
              bbox_to_anchor=(0.5, -0.08), frameon=True, fontsize=22)
    
    plt.tight_layout()
    # Adjust layout to make room for model name on the left if present
    if model_name:
        plt.subplots_adjust(bottom=0.15, top=0.80, left=0.08)
    else:
        plt.subplots_adjust(bottom=0.15, top=0.80)
    
    # Save plot
    if save_path:
        # Use SVG format for vector graphics (smaller size, scalable)
        svg_path = save_path.replace('.png', '.svg')
        plt.savefig(svg_path, format='svg', bbox_inches='tight')
        logger.info(f"Saved combined embedding figure to {svg_path}")
        
        # Also save PNG for compatibility if needed
        png_path = save_path.replace('.svg', '.png')  
        plt.savefig(png_path, format='png', dpi=150, bbox_inches='tight')
        logger.info(f"Also saved PNG version to {png_path}")
    
    if show:
        plt.show()
    
    return fig


def create_all_models_combined_figure(models_data: Dict[str, pd.DataFrame],
                                     gene_symbol: str,
                                     figsize: Tuple[int, int] = (20, 18),
                                     save_path: Optional[str] = None,
                                     show: bool = False,
                                     title: Optional[str] = None) -> plt.Figure:
    """
    Create a combined figure showing embedding results for all models in a grid.
    Each row represents a model, each column represents a dimension reduction method.
    
    Args:
        models_data: Dictionary mapping model names to DataFrames with columns:
                    variant_id, pca_x, pca_y, t-sne_x, t-sne_y, umap_x, umap_y, labels
        gene_symbol: Gene symbol for the title (e.g., 'BRCA1', 'FBN1')
        figsize: Figure size (width, height)
        save_path: Path to save the combined plot
        show: Whether to display the plot
        title: Optional custom title for the figure. If None, generates title automatically.
        
    Returns:
        Matplotlib figure object
    """
    # Check that all DataFrames have required 'labels' column
    for model_name, df in models_data.items():
        if 'labels' not in df.columns:
            raise ValueError(f"DataFrame for model '{model_name}' must have a column named 'labels'")
    
    methods = ['PCA', 't-SNE', 'UMAP']  # Standard order for titles
    method_columns = ['pca', 't-sne', 'umap']  # Column names in your data (with hyphen for t-sne)
    
    # Get model names in order (preserve insertion order if Python 3.7+)
    model_names = list(models_data.keys())
    num_models = len(model_names)
    
    if num_models == 0:
        raise ValueError("No models data provided")
    
    # Create figure with subplots (num_models rows, 3 columns)
    fig, axes = plt.subplots(num_models, 3, figsize=figsize)
    
    # Handle case where there's only one model (axes becomes 1D)
    if num_models == 1:
        axes = axes.reshape(1, -1)
    
    # Use comprehensive color map
    color_map = COMPREHENSIVE_PATHOGENICITY_COLORS
    
    # Collect all unique labels across all models for consistent legend
    all_labels = set()
    for df in models_data.values():
        all_labels.update(df['labels'].unique())
    unique_labels = sorted(all_labels)
    
    # Count known and unknown variants from all data combined
    # Use first model's data for counts (all models should have same variants)
    first_df = list(models_data.values())[0]
    known_labels = [label for label in unique_labels if label not in ['query', 'unknown', 'not_yet_reviewed']]
    unknown_labels = [label for label in unique_labels if label in ['query', 'unknown', 'not_yet_reviewed']]
    
    known_count = first_df['labels'].isin(known_labels).sum()
    unknown_count = first_df['labels'].isin(unknown_labels).sum()
    
    # Create legend elements with special handling for test variants
    legend_elements = []
    for label in unique_labels:
        color = color_map.get(label, "#888888")
        
        # Special styling for test variants (query/unknown)
        if label in ['query', 'unknown', 'not_yet_reviewed']:
            legend_elements.append(Line2D([0], [0], marker='D', color='w',
                                         markerfacecolor=color, markersize=10,
                                         markeredgecolor='black', markeredgewidth=1.0,
                                         label=f'{label} (unknown)', alpha=0.9))
        else:
            legend_elements.append(Line2D([0], [0], marker='o', color='w',
                                         markerfacecolor=color, markersize=12, 
                                         label=label, alpha=0.7))
    
    # Plot each model (row) and each method (column)
    for row_idx, model_name in enumerate(model_names):
        merged_df = models_data[model_name]
        
        for col_idx, (method_title, method_col) in enumerate(zip(methods, method_columns)):
            ax = axes[row_idx, col_idx]
            
            # Get coordinates for this method
            x_col = f"{method_col}_x"
            y_col = f"{method_col}_y"
            
            if x_col in merged_df.columns and y_col in merged_df.columns:
                # Filter out NaN values
                valid_mask = merged_df[x_col].notna() & merged_df[y_col].notna()
                
                # Debug: Print counts for each label
                if row_idx == 0 and col_idx == 0:  # Only print once per model
                    print(f"\nDebug info for {model_name} - {method_title}:")
                    for label in unique_labels:
                        total_count = (merged_df['labels'] == label).sum()
                        valid_count = ((merged_df['labels'] == label) & valid_mask).sum()
                        print(f"  {label}: {valid_count}/{total_count} variants with valid coordinates")
                
                if valid_mask.any():
                    # Plot each class
                    for label in unique_labels:
                        mask = (merged_df['labels'] == label) & valid_mask
                        if mask.any():
                            color = color_map.get(label, "#888888")
                            
                            # Special styling for test variants (query/unknown)
                            if label in ['query', 'unknown', 'not_yet_reviewed']:
                                # Use diamond markers with black edge for test variants
                                ax.scatter(merged_df.loc[mask, x_col], merged_df.loc[mask, y_col], 
                                          c=color, alpha=0.9, s=50, marker='D', 
                                          edgecolors='black', linewidths=1.0)
                            else:
                                # Use circle markers for training variants (increased size for visibility)
                                ax.scatter(merged_df.loc[mask, x_col], merged_df.loc[mask, y_col], 
                                          c=color, alpha=0.8, s=25, marker='o', edgecolors='none')
                    
                    # Set labels and grid
                    ax.set_xlabel('Component 1', fontsize=14)
                    ax.set_ylabel('Component 2', fontsize=14)
                    ax.grid(True, alpha=0.3)
                    
                    # Add method title only on top row
                    if row_idx == 0:
                        ax.set_title(f'{method_title}', fontsize=18, fontweight='bold', pad=20)
                
                else:
                    # Handle case with no valid data
                    ax.text(0.5, 0.5, f'{method_title}\nNo valid data', ha='center', va='center',
                           transform=ax.transAxes, fontsize=14, color='gray')
                    ax.set_xticks([])
                    ax.set_yticks([])
                    if row_idx == 0:
                        ax.set_title(f'{method_title}', fontsize=18, fontweight='bold', pad=20)
            else:
                # Handle missing columns
                ax.text(0.5, 0.5, f'{method_title}\nMissing columns', ha='center', va='center',
                       transform=ax.transAxes, fontsize=14, color='gray')
                ax.set_xticks([])
                ax.set_yticks([])
                if row_idx == 0:
                    ax.set_title(f'{method_title}', fontsize=18, fontweight='bold', pad=20)
        
        # Add model name on the left side (further increased distance from plots)
        axes[row_idx, 0].text(-0.25, 0.5, model_name, rotation=90, ha='center', va='center',
                               transform=axes[row_idx, 0].transAxes, fontsize=20, fontweight='bold')
    
    # Set main title (increased distance from plots) with gene name formatted as bold italic
    if title is None:
        total_variants = known_count + unknown_count
        figure_title = f'Embedding results of {gene_symbol} - {known_count} known + {unknown_count} unknown variants'
    else:
        figure_title = title
    format_gene_name_in_title(fig, figure_title, gene_symbol, y_pos=0.95, fontsize=28)
    
    # Add legend at the bottom (increased font size)
    fig.legend(handles=legend_elements, loc='lower center', ncol=len(legend_elements), 
              bbox_to_anchor=(0.5, -0.01), frameon=True, fontsize=22)
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.08, top=0.85, left=0.12)
    
    # Save plot
    if save_path:
        # Use SVG format for vector graphics (smaller size, scalable)
        svg_path = save_path.replace('.png', '.svg')
        plt.savefig(svg_path, format='svg', bbox_inches='tight')
        logger.info(f"Saved all-models combined embedding figure to {svg_path}")
        
        # Also save PNG for compatibility if needed
        png_path = save_path.replace('.svg', '.png')  
        plt.savefig(png_path, format='png', dpi=150, bbox_inches='tight')
        logger.info(f"Also saved PNG version to {png_path}")
    
    if show:
        plt.show()
    
    return fig
