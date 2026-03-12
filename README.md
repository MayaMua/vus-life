# VUS.LIFE: Your Super-Fast Assistant for Variant Classification! 🧬✨

Ever feel like you're drowning in a sea of VUS (Variants of Uncertain Significance)? Wish you had a magic wand to sort them out? Well, we've got the next best thing!

**VUS.LIFE** is here to take the heavy lifting out of variant analysis. Think of it as your personal genomics wizard. Just give it the standard variant annotations, and with a single click, it zips through mountains of data to predict whether a variant is pathogenic or benign. No more manual sifting, no more headaches!

We've put VUS.LIFE to the test on well-studied genes like _BRCA1_, _BRCA2_, and _FBN1_, and it's already acing the exam with **over 96% accuracy**. It's fast, reliable, and ready to help you make sense of your data in record time.

Ready to see the magic in action?

👉 **[Check out the detailed performance results here!](Results/README.md)**

---

### 🤖 AI Interpretation (API)

The **AI interpretation** feature provides a **skeptical second-opinion** on VUS_LIFE’s embedding-based predictions. It compares the target variant (unknown significance) against its neighbor variants (known pathogenicity) and performs a **discordance check**: it evaluates whether the target truly shares the same pathogenic mechanism as the neighbors by checking functional impact and amino acid changes, concordance of computational scores (e.g. AlphaMissense, EVE, SpliceAI), and physicochemical properties of the substitutions. Embedding models can cluster variants by gene, exon, or location rather than by real biological mechanism, so this step helps flag cases where the embedding prediction may be misleading and supports more reliable variant interpretation.

---

🚀 Want to Try It Yourself?
Excited to take VUS.LIFE for a spin? A user-friendly desktop app is coming soon! You can try a beta version via: 👉 **[vus-life-beta](http://vus.life/)**.

📖 **[Read the Web App User Guide](WEB_APP_GUIDE.md)** for detailed instructions on how to use the beta version.

To be the first to know when the desktop app drops, click the "Watch" button at the top of this page. You'll get a notification the moment it's released!

---

### 📜 Read The Paper

For a deep dive into how it all works, you can read our full paper [Link](https://www.researchsquare.com/article/rs-8605164/v1):
**Predicting Genetic Variant Pathogenicity Using Vector Embeddings**

### 📜 Patent

U.S. Provisional Patent Application No. 63/821,249, filed June 10, 2025.

### Acknowledgments
