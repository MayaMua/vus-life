# Frontend Tags Module

This directory contains modular display components for the variant processing dashboard. Each module handles the display logic for specific types of results, making the code more maintainable and reusable.

## Files

### `common_utils.py`

Shared utility functions used across all display modules to avoid code duplication.

**Purpose**: Provides common functionality for loading training metadata and pathogenicity mappings from cache.

**Main Functions**:

1. **`load_training_metadata_from_cache(gene_symbol, config, get_user_training_metadata_dir_func)`**
   - Loads training metadata from cached JSON file
   - Returns metadata dictionary or None if not found
   - Handles errors gracefully with warnings

2. **`load_pathogenicity_mapping(gene_symbol, config, get_user_training_metadata_dir_func)`**
   - Extracts pathogenicity mapping from training metadata
   - Returns dictionary mapping variant_id to pathogenicity_original
   - Used by embedding plots for variant labeling

**Usage**:

```python
from frontend.tags.common_utils import (
    load_training_metadata_from_cache,
    load_pathogenicity_mapping
)

# Load metadata
metadata = load_training_metadata_from_cache(gene_symbol, config, get_metadata_dir_func)

# Load pathogenicity mapping
pathogenicity_map = load_pathogenicity_mapping(gene_symbol, config, get_metadata_dir_func)
```

### `display_training_variants.py`

Handles the display and retrieval of training variants metadata.

**Purpose**: Provides reusable functions for loading, fetching, and displaying training variants metadata from cache or API.

**Main Functions**:

1. **`load_or_fetch_metadata(gene_symbol, config, get_metadata_gene_func, get_user_training_metadata_dir_func)`**
   - Loads metadata from cached JSON file if available
   - Falls back to fetching from API if cache miss or error
   - Automatically saves fetched data to cache
   - Returns metadata dictionary or None on error

2. **`handle_get_training_variants_button(gene_symbol, config, get_metadata_gene_func, get_user_training_metadata_dir_func)`**
   - Handles the "Get Training Variants" button click event
   - Validates gene symbol
   - Manages session state (clears old data when gene changes)
   - Loads/fetches metadata with loading spinner
   - Shows success/error messages
   - Forces Streamlit rerun to display new tab

3. **`render_get_training_variants_button(config, gene_symbol, get_metadata_gene_func, get_user_training_metadata_dir_func, use_container_width)`**
   - All-in-one function that renders the button AND handles click
   - Useful for standalone pages or simplified integration

**Usage in main app**:

```python
from frontend.tags.display_training_variants import handle_get_training_variants_button

# In sidebar: render button manually
get_metadata_btn = st.button("Get Training Variants", use_container_width=True)

# Later in main content: handle button click
if get_metadata_btn:
    handle_get_training_variants_button(
        gene_symbol=gene_symbol,
        config=config,
        get_metadata_gene_func=get_metadata_gene,
        get_user_training_metadata_dir_func=get_user_training_metadata_dir
    )
```

### `display_embedding_plots.py`

Handles the display of embedding visualization plots (PCA, t-SNE, UMAP).

**Purpose**: Provides modular functions for loading coordinates and rendering embedding plots for variant visualization.

**Main Functions**:

1. **`display_embedding_plots(prediction_results, gene_symbol, config, get_user_training_metadata_dir_func)`**
   - Main function to render embedding plots
   - Defaults to selecting ALL models
   - No K value selection (uses fixed k=5 internally)
   - Handles single and multi-model visualizations

2. **`load_training_coordinates(gene_symbol, embedding_model_name, annotation_method, config, get_user_training_metadata_dir_func, label_mapping)`**
   - Loads training variant coordinates from parquet files
   - Applies pathogenicity labeling (binary or detailed)
   - Returns DataFrame with coordinates and labels

3. **`load_query_coordinates_from_response(prediction_results, embedding_model_name)`**
   - Extracts query variant coordinates from prediction results
   - Handles PCA, t-SNE, and UMAP coordinates
   - Returns DataFrame formatted for plotting

4. **`load_training_pathogenicity_mapping(gene_symbol, config, get_user_training_metadata_dir_func)`**
   - Loads pathogenicity labels from metadata
   - Returns mapping of variant_id to pathogenicity_original

**Usage in main app**:

```python
from frontend.tags.display_embedding_plots import display_embedding_plots

# Inside a Streamlit tab
with tabs[tab_idx]:
    display_embedding_plots(
        prediction_results=st.session_state.prediction_results,
        gene_symbol=gene_symbol,
        config=config,
        get_user_training_metadata_dir_func=get_user_training_metadata_dir
    )
```

### `display_prediction_results.py`

Handles the display of prediction results including existing and new variants.

**Purpose**: Provides modular functions for rendering prediction results with comprehensive variant information and model summaries.

**Main Functions**:

1. **`display_prediction_results(prediction_results, training_metadata, gene_symbol, job_name, prediction_results_to_df_func, config, get_user_training_metadata_dir_func, k_value)`**
   - Main function to render all prediction results
   - Displays metrics for existing vs new variants
   - Orchestrates display of existing variants, new variants, and model summaries
   - Handles loading of training metadata if not provided

2. **`display_existing_variants(existing_variants, training_metadata, gene_symbol)`**
   - Displays variants that are already in the database
   - Shows full metadata if training data is available
   - Falls back to showing just variant IDs if metadata unavailable

3. **`display_new_variants(new_variants, prediction_results_dict, existing_variants, model_names, training_metadata, gene_symbol, job_name, prediction_results_to_df_func, k_value)`**
   - Displays newly processed variants with predictions
   - Converts prediction results to DataFrame format
   - Handles ClinVar data integration
   - Shows summary statistics

4. **`display_model_summary(model_names, prediction_results_dict)`**
   - Displays summary of model processing results
   - Shows success/error counts for each model
   - Provides at-a-glance view of processing status

**Usage in main app**:

```python
from frontend.tags.display_prediction_results import display_prediction_results

# Inside a Streamlit tab
with tabs[tab_idx]:
    if st.session_state.prediction_results:
        display_prediction_results(
            prediction_results=st.session_state.prediction_results,
            training_metadata=st.session_state.metadata_results,
            gene_symbol=gene_symbol,
            job_name=job_name,
            prediction_results_to_df_func=prediction_results_to_df,
            config=config,
            get_user_training_metadata_dir_func=get_user_training_metadata_dir,
            k_value=5
        )
```

## Design Philosophy

These modules follow the separation of concerns principle:

- **Display logic** is separated from the main app logic
- **Reusability** is maximized through modular functions
- **Maintainability** is improved with clear function signatures and documentation
- **Testing** is easier with isolated display components
- **Dependency injection** avoids circular imports and maintains flexibility

## Integration with app.py

The main `app.py` file imports these modules and uses them within Streamlit tabs to display different types of results. This architecture allows for:

- ✅ Easy updates to display logic without touching main app code
- ✅ Consistent display patterns across different result types
- ✅ Better code organization and readability
- ✅ Modular testing capabilities
- ✅ Reusable components across different views

## Benefits of Tag-Based Display

By organizing display components as "tags" (modular units), we achieve:

1. **Clear separation**: Each file handles one specific display concern
2. **Easy navigation**: Developers can quickly find and update specific display logic
3. **Reduced complexity**: Main app.py is cleaner and more focused on orchestration
4. **Flexible composition**: Display components can be easily rearranged or combined
5. **Independent development**: Team members can work on different display modules without conflicts
