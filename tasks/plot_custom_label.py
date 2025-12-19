#!/usr/bin/env python3
"""
Plot existing and new variants with custom labels (e.g. HCD categories).

Inputs (CLI):
    gene_symbol: e.g. FBN1
    model_name: e.g. all-mpnet-base-v2
    task_name: e.g. query_2

This script will:
1. Load existing variant IDs from existing_variants.json.
2. Join existing variant metadata from metadata.json.
3. Join existing variant coordinates from the coordinates parquet.
4. Load new variants (prediction results) and their coordinates.
5. Concatenate existing + new variants into a single DataFrame.
6. Merge custom labels (HCD) from the corresponding *_test.csv file.
7. Map HCD to two categories: "Disulfide bonds" and "Ca2+ binding".
8. Plot PCA / t-SNE / UMAP embeddings for the selected model, colored by HCD group.

The plotting style is inspired by frontend/utils/embedding_visualization.py,
but adapted to use custom labels instead of pathogenicity categories.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd


# -----------------------------------------------------------------------------
# Project root and imports
# -----------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from frontend.utils.parquet_manager import CoordinateParquetManager  # noqa: E402


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Data loading helpers
# -----------------------------------------------------------------------------

def _get_paths(
    gene_symbol: str,
    model_name: str,
    task_name: str,
    annotation_method: str = "vep",
) -> Dict[str, Path]:
    """
    Build all file paths needed for a given gene / model / task.
    """
    # User-query specific paths
    results_dir = (
        PROJECT_ROOT
        / "data_user"
        / "user_query"
        / "results"
        / gene_symbol
        / task_name
        / f"{model_name}_{annotation_method}"
    )

    existing_variants_path = results_dir / "existing_variants.json"
    prediction_results_path = results_dir / "prediction_results.json"

    # Training metadata and coordinates
    metadata_path = (
        PROJECT_ROOT
        / "data_user"
        / "training_embedding_results"
        / "metadata"
        / gene_symbol
        / "metadata.json"
    )

    coordinates_path = (
        PROJECT_ROOT
        / "data_user"
        / "training_embedding_results"
        / "coordinates"
        / gene_symbol
        / f"{gene_symbol}_{annotation_method}_coordinates.parquet"
    )

    # Label CSV (HCD)
    label_csv_path = (
        PROJECT_ROOT
        / "data_user"
        / "user_query"
        / "inputs"
        / gene_symbol
        / task_name
        / f"{gene_symbol}_test.csv"
    )

    # Output directory for plots and concatenated data
    output_dir = results_dir

    return {
        "existing_variants": existing_variants_path,
        "prediction_results": prediction_results_path,
        "metadata": metadata_path,
        "coordinates": coordinates_path,
        "label_csv": label_csv_path,
        "output_dir": output_dir,
    }


def load_existing_variants_with_coords(
    gene_symbol: str,
    model_name: str,
    task_name: str,
    annotation_method: str = "vep",
) -> pd.DataFrame:
    """
    Load existing variants, join metadata and coordinates for the given model.

    Returns:
        DataFrame with columns:
            chromosome, position, ref_allele, alt_allele,
            hgvs_genomic_38, most_severe_consequence,
            {model_name}_pca_x, {model_name}_pca_y,
            {model_name}_t-sne_x, {model_name}_t-sne_y,
            {model_name}_umap_x, {model_name}_umap_y,
            source
    """
    paths = _get_paths(gene_symbol, model_name, task_name, annotation_method)

    if not paths["existing_variants"].exists():
        logger.warning(f"existing_variants.json not found: {paths['existing_variants']}")
        return pd.DataFrame()

    if not paths["metadata"].exists():
        logger.warning(f"metadata.json not found: {paths['metadata']}")
        return pd.DataFrame()

    if not paths["coordinates"].exists():
        logger.warning(f"Coordinates parquet not found: {paths['coordinates']}")
        return pd.DataFrame()

    # Load existing variant IDs
    with paths["existing_variants"].open("r") as f:
        existing_data = json.load(f)
    existing_ids: List[str] = existing_data.get("variants", [])

    if not existing_ids:
        logger.info("No existing variant IDs found.")
        return pd.DataFrame()

    # Load metadata variants
    with paths["metadata"].open("r") as f:
        metadata_data = json.load(f)
    metadata_variants = metadata_data.get("variants") or metadata_data.get("query_variant") or []

    df_meta = pd.DataFrame(metadata_variants)
    if df_meta.empty:
        logger.warning("Metadata variants DataFrame is empty.")
        return pd.DataFrame()

    df_meta_existing = df_meta[df_meta["variant_id"].isin(existing_ids)].copy()
    if df_meta_existing.empty:
        logger.warning("No metadata rows matched existing variant IDs.")
        return pd.DataFrame()

    # Load coordinates for the selected model
    coord_manager = CoordinateParquetManager(str(paths["coordinates"]))
    try:
        df_coords = coord_manager.get_coordinates_for_model(model_name)
    except FileNotFoundError:
        logger.warning(f"Coordinates parquet file not found: {paths['coordinates']}")
        return pd.DataFrame()

    if df_coords.empty:
        logger.warning(f"No coordinates found for model {model_name}.")
        return pd.DataFrame()

    # Merge metadata with coordinates on variant_id
    df_merged = df_meta_existing.merge(df_coords, on="variant_id", how="left")

    # Rename coordinate columns to include model_name prefix
    coord_cols = ["pca_x", "pca_y", "t-sne_x", "t-sne_y", "umap_x", "umap_y"]
    rename_map = {
        col: f"{model_name}_{col}"
        for col in coord_cols
        if col in df_merged.columns
    }
    df_merged = df_merged.rename(columns=rename_map)

    # Keep only necessary columns
    keep_cols = [
        "chromosome",
        "position",
        "ref_allele",
        "alt_allele",
        "hgvs_genomic_38",
        "most_severe_consequence",
    ] + list(rename_map.values())

    keep_cols = [c for c in keep_cols if c in df_merged.columns]
    df_final = df_merged[keep_cols].copy()
    df_final["source"] = "existing"

    # Ensure consistent dtypes
    if "position" in df_final.columns:
        df_final["position"] = pd.to_numeric(df_final["position"], errors="coerce").astype("Int64")

    return df_final


def load_new_variants_with_coords(
    gene_symbol: str,
    model_name: str,
    task_name: str,
    annotation_method: str = "vep",
) -> pd.DataFrame:
    """
    Load new variants (prediction_results.json) and extract coordinates.

    Returns:
        DataFrame with the same columns as load_existing_variants_with_coords, plus:
            source = "new"
    """
    paths = _get_paths(gene_symbol, model_name, task_name, annotation_method)

    if not paths["prediction_results"].exists():
        logger.warning(f"prediction_results.json not found: {paths['prediction_results']}")
        return pd.DataFrame()

    with paths["prediction_results"].open("r") as f:
        data = json.load(f)

    if "successful" in data:
        results = data["successful"].get("results", [])
    else:
        results = data.get("results", [])

    if not results:
        logger.warning("No results found in prediction_results.json.")
        return pd.DataFrame()

    rows: List[Dict[str, Any]] = []

    for result in results:
        metadata = result.get("metadata", {})
        coordinates_list = result.get("coordinates", [])

        # Flatten coordinates list into a single dict: {pca_x, pca_y, t-sne_x, ...}
        coord_values: Dict[str, float] = {}
        for coord_dict in coordinates_list:
            for key, value in coord_dict.items():
                coord_values[key] = value

        row: Dict[str, Any] = {
            "chromosome": metadata.get("chromosome", ""),
            "position": metadata.get("position", ""),
            "ref_allele": metadata.get("ref_allele", ""),
            "alt_allele": metadata.get("alt_allele", ""),
            "hgvs_genomic_38": metadata.get("hgvs_genomic_38", ""),
            "most_severe_consequence": metadata.get("most_severe_consequence", ""),
            "source": "new",
        }

        # Attach model-specific coordinate columns
        for base_col in ["pca_x", "pca_y", "t-sne_x", "t-sne_y", "umap_x", "umap_y"]:
            value = coord_values.get(base_col)
            row[f"{model_name}_{base_col}"] = value

        rows.append(row)

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    # Ensure numeric position
    if "position" in df.columns:
        df["position"] = pd.to_numeric(df["position"], errors="coerce").astype("Int64")

    return df


def load_and_merge_labels(
    df_variants: pd.DataFrame,
    gene_symbol: str,
    task_name: str,
    annotation_method: str,
    model_name: str,
) -> pd.DataFrame:
    """
    Merge HCD labels from *_test.csv into the variants DataFrame.

    The merge is performed on:
        chromosome, position, ref_allele, alt_allele

    Also creates a new column 'HCD_group' with two categories:
        - "Disulfide bonds" if HCD contains this phrase
        - "Ca2+ binding" if HCD contains this phrase
        - None otherwise
    """
    paths = _get_paths(gene_symbol, model_name, task_name, annotation_method)

    if df_variants.empty:
        logger.warning("Variant DataFrame is empty, skipping label merge.")
        return df_variants

    if not paths["label_csv"].exists():
        logger.warning(f"Label CSV not found: {paths['label_csv']}")
        return df_variants

    df_labels = pd.read_csv(paths["label_csv"])
    required_cols = {"chromosome", "position", "ref_allele", "alt_allele", "HCD"}
    missing = required_cols - set(df_labels.columns)
    if missing:
        logger.warning(f"Label CSV missing columns: {missing}")
        return df_variants

    # Ensure consistent dtypes for merge keys
    for col in ["chromosome", "ref_allele", "alt_allele"]:
        df_variants[col] = df_variants[col].astype(str)
        df_labels[col] = df_labels[col].astype(str)

    df_variants["position"] = pd.to_numeric(df_variants["position"], errors="coerce").astype("Int64")
    df_labels["position"] = pd.to_numeric(df_labels["position"], errors="coerce").astype("Int64")

    merge_keys = ["chromosome", "position", "ref_allele", "alt_allele"]
    df_merged = df_variants.merge(
        df_labels[merge_keys + ["HCD"]],
        on=merge_keys,
        how="left",
    )

    # Map HCD to two-category group
    def _map_hcd_to_group(hcd: Any) -> Optional[str]:
        """Map raw HCD string to one of the target groups (case-insensitive)."""
        if not isinstance(hcd, str):
            return None
        hcd_lower = hcd.lower()
        if "disulfide bonds" in hcd_lower:
            return "Disulfide bonds"
        if "ca2+ binding" in hcd_lower:
            return "Ca2+ binding"
        return None

    df_merged["HCD_group"] = df_merged["HCD"].apply(_map_hcd_to_group)

    logger.info(
        "Label summary: "
        f"Disulfide bonds = { (df_merged['HCD_group'] == 'Disulfide bonds').sum() }, "
        f"Ca2+ binding = { (df_merged['HCD_group'] == 'Ca2+ binding').sum() }"
    )

    return df_merged


# -----------------------------------------------------------------------------
# Plotting
# -----------------------------------------------------------------------------

def plot_embeddings_with_hcd(
    df: pd.DataFrame,
    gene_symbol: str,
    model_name: str,
    save_path: Path,
    show: bool = False,
) -> plt.Figure:
    """
    Plot PCA / t-SNE / UMAP embeddings for a single model, colored by HCD_group.

    The DataFrame is expected to contain columns:
        {model_name}_pca_x, {model_name}_pca_y, ...
        HCD_group (two categories: Disulfide bonds, Ca2+ binding)
    """
    if df.empty:
        raise ValueError("Input DataFrame for plotting is empty.")

    # Prepare a copy with generic coordinate column names
    coord_bases = ["pca_x", "pca_y", "t-sne_x", "t-sne_y", "umap_x", "umap_y"]
    working_df = df.copy()

    for base in coord_bases:
        col_with_model = f"{model_name}_{base}"
        if col_with_model in working_df.columns:
            working_df[base] = working_df[col_with_model]

    # Filter rows that have labels of interest
    working_df = working_df[working_df["HCD_group"].notna()].copy()
    if working_df.empty:
        raise ValueError("No rows with HCD_group labels found after filtering.")

    # Drop rows with missing coordinates for safety
    coord_pairs = [("pca_x", "pca_y"), ("t-sne_x", "t-sne_y"), ("umap_x", "umap_y")]
    for x_col, y_col in coord_pairs:
        if x_col in working_df.columns and y_col in working_df.columns:
            mask = working_df[x_col].notna() & working_df[y_col].notna()
            working_df = working_df[mask]

    if working_df.empty:
        raise ValueError("No valid coordinate rows available for plotting.")

    methods = ["PCA", "t-SNE", "UMAP"]
    method_columns = ["pca", "t-sne", "umap"]

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Color map for two categories
    color_map = {
        "Disulfide bonds": "#DB3124",  # Red
        "Ca2+ binding": "#4B74B2",     # Blue
    }

    unique_labels = sorted(working_df["HCD_group"].dropna().unique())

    legend_elements: List[Line2D] = []
    for label in unique_labels:
        color = color_map.get(label, "#888888")
        legend_elements.append(
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                markerfacecolor=color,
                markersize=10,
                label=label,
                alpha=0.8,
            )
        )

    # Plot each method
    for i, (method_title, method_col) in enumerate(zip(methods, method_columns)):
        ax = axes[i]
        x_col = f"{method_col}_x"
        y_col = f"{method_col}_y"

        if x_col not in working_df.columns or y_col not in working_df.columns:
            ax.text(
                0.5,
                0.5,
                f"{method_title}\nMissing columns",
                ha="center",
                va="center",
                transform=ax.transAxes,
                fontsize=14,
                color="gray",
            )
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title(method_title, fontsize=16, fontweight="bold")
            continue

        for label in unique_labels:
            mask = working_df["HCD_group"] == label
            if not mask.any():
                continue

            color = color_map.get(label, "#888888")
            ax.scatter(
                working_df.loc[mask, x_col],
                working_df.loc[mask, y_col],
                c=color,
                alpha=0.8,
                s=20,
                marker="o",
            )

        ax.set_xlabel("Component 1", fontsize=12)
        ax.set_ylabel("Component 2", fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.set_title(method_title, fontsize=16, fontweight="bold")

    fig.suptitle(
        f"{gene_symbol} embeddings ({model_name}) with HCD groups",
        fontsize=18,
        fontweight="bold",
        y=0.98,
    )

    fig.legend(
        handles=legend_elements,
        loc="lower center",
        ncol=len(legend_elements),
        bbox_to_anchor=(0.5, -0.12),
        frameon=True,
        fontsize=12,
    )

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.22, top=0.88)

    # Save both SVG and PNG
    save_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path = save_path.with_suffix(".svg")
    png_path = save_path.with_suffix(".png")

    fig.savefig(svg_path, format="svg", bbox_inches="tight")
    fig.savefig(png_path, format="png", dpi=150, bbox_inches="tight")

    logger.info(f"Saved HCD embedding figure (SVG) to {svg_path}")
    logger.info(f"Saved HCD embedding figure (PNG) to {png_path}")

    if show:
        plt.show()

    return fig


# -----------------------------------------------------------------------------
# Main orchestration
# -----------------------------------------------------------------------------

def run_plot_custom_label(
    gene_symbol: str,
    model_name: str,
    task_name: str,
    annotation_method: str = "vep",
    show: bool = False,
) -> pd.DataFrame:
    """
    High-level pipeline:
    - Load existing + new variants with coordinates.
    - Concatenate.
    - Merge HCD labels and map to two categories.
    - Plot embeddings for the specified model.

    Returns:
        Final merged DataFrame used for plotting.
    """
    logger.info(
        f"Running custom-label plot for gene={gene_symbol}, "
        f"model={model_name}, task={task_name}, annotation={annotation_method}"
    )

    df_existing = load_existing_variants_with_coords(
        gene_symbol=gene_symbol,
        model_name=model_name,
        task_name=task_name,
        annotation_method=annotation_method,
    )
    logger.info(f"Existing variants shape: {df_existing.shape}")

    df_new = load_new_variants_with_coords(
        gene_symbol=gene_symbol,
        model_name=model_name,
        task_name=task_name,
        annotation_method=annotation_method,
    )
    logger.info(f"New variants shape: {df_new.shape}")

    df_all = pd.concat([df_existing, df_new], ignore_index=True, sort=False)
    logger.info(f"Concatenated variants shape: {df_all.shape}")

    # Merge labels
    df_labeled = load_and_merge_labels(
        df_variants=df_all,
        gene_symbol=gene_symbol,
        task_name=task_name,
        annotation_method=annotation_method,
        model_name=model_name,
    )

    # Save concatenated DataFrame for downstream inspection
    paths = _get_paths(gene_symbol, model_name, task_name, annotation_method)
    paths["output_dir"].mkdir(parents=True, exist_ok=True)
    concat_csv_path = paths["output_dir"] / f"{gene_symbol}_{model_name}_{task_name}_HCD_merged.csv"
    df_labeled.to_csv(concat_csv_path, index=False)
    logger.info(f"Saved concatenated labeled DataFrame to {concat_csv_path}")

    # Plot
    plot_save_path = paths["output_dir"] / f"{gene_symbol}_{model_name}_{task_name}_HCD_embeddings"
    plot_embeddings_with_hcd(
        df=df_labeled,
        gene_symbol=gene_symbol,
        model_name=model_name,
        save_path=plot_save_path,
        show=show,
    )

    return df_labeled


def _parse_args(argv: List[str]) -> Tuple[str, str, str]:
    """
    Simple CLI argument parser for:
        gene_symbol, model_name, task_name
    """
    if len(argv) < 4:
        raise SystemExit(
            "Usage: python tasks/plot_custom_label.py "
            "<gene_symbol> <model_name> <task_name>\n"
            "Example:\n"
            "  python tasks/plot_custom_label.py FBN1 all-mpnet-base-v2 query_2"
        )
    gene_symbol = argv[1]
    model_name = argv[2]
    task_name = argv[3]
    return gene_symbol, model_name, task_name


if __name__ == "__main__":
    gene, model, task = _parse_args(sys.argv)
    run_plot_custom_label(
        gene_symbol=gene,
        model_name=model,
        task_name=task,
        annotation_method="vep",
        show=False,
    )


