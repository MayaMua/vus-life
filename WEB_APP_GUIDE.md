# VUS.LIFE Web App User Guide

## Overview

This application provides variant pathogenicity prediction and embedding visualization for genetic variants using machine learning models. 

**Access the app here:** [http://98.92.58.214:8501/](http://98.92.58.214:8501/)

---

## Important Usage Notes

### 1. Input Format Requirements

- Currently accepts only **g. annotation format** (genomic notation)
- **Variants must be from the same gene** in a single query
  - ✅ Example: Query BRCA1 variants separately from BRCA2 variants
  - ❌ Do not mix variants from different genes

### 2. Query Limitations

- Please limit your input to **maximum 10 variants per query**
- While the app won't crash with more variants, processing time will significantly increase

### 3. Gene Selection

- On the preview input page, verify that your **selected gene in the sidebar matches the gene in your uploaded variants**
- This is crucial for accurate predictions

### 4. Processing

- Click **"Process Variants"** to start the prediction

### 5. Results Interpretation

The results page contains two sections:

- **Existing Variants**: Variants from your input that already exist in the training dataset with known pathogenicity labels
- **New Variants**: Variants from your input not present in the training dataset, which will be predicted as having unknown pathogenicity

### 6. Embedding Plot

- View the 2D spatial distribution of your input variants' mathematical representations
- This visualization shows how known variants cluster in the embedding space

---

## Test Data

Test data files are available for **BRCA1**, **BRCA2**, and **FBN1** genes.

### Important Notes:

- ⚠️ **Manual input is currently experiencing a bug and is not functional**
- Please use **file upload** instead
- The provided files contain hundreds of variants
- **Recommended**: Select approximately 10 variants and save them to a `.txt` file for testing

---

## Feedback & Support

Thank you for trying this app! Your feedback and comments are greatly appreciated. 

If you encounter any issues, please feel free to contact me or open an issue on this repository.
