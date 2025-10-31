import json
import os
from dotenv import load_dotenv
import numpy as np
import pandas as pd
import requests
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA
from umap import UMAP
from hdbscan import HDBSCAN
from sklearn.cluster import KMeans
import plotly.express as px
import matplotlib.pyplot as plt
from test import filter_text_final_version

df = pd.read_csv('data/data.csv')
titles = df['Phrase'].tolist()

texts_list = [filter_text_final_version(text) for text in titles]

abstracts = texts_list

model = SentenceTransformer('all-MiniLM-L12-v2')
embeddings = model.encode(texts_list, device='cuda')
# embeddings = get_embedding(texts_list)

print(embeddings.shape)

umap_model = UMAP(
    n_components=8, # Reduces dimensionality while preserving essential structure
    min_dist=0.0, # Controls how tightly points cluster together
    metric='cosine', # Measures similarity between embeddings using cosine distance
    random_state=42
)

reduced_embeddings = umap_model.fit_transform(embeddings)

print(f"Shape of reduced embeddings: {reduced_embeddings.shape}")

# We fit the model and extract the clusters
hdbscan_model = HDBSCAN(
    min_cluster_size=50, # Ensures statistically significant groupings
    metric='euclidean', # Measures distance in reduced space
    cluster_selection_method='eom' # Optimizes cluster boundary detection
).fit(reduced_embeddings)
clusters = hdbscan_model.labels_

# How many clusters did we generate?
print(f"Number of clusters: {len(set(clusters))}")


# Print first three documents in cluster 0
cluster = 2
for index in np.where(clusters==cluster)[0]:
    print(abstracts[index][:300] + "... \n")


# Reduce 384-dimensional embeddings to 3 dimensions
reduced_embeddings_3d = UMAP(
   n_components=3,
   min_dist=0.0,
   metric='cosine',
   random_state=42
).fit_transform(embeddings)

# Create dataframe with 3D coordinates
df_3d = pd.DataFrame(
   reduced_embeddings_3d,
   columns=["x", "y", "z"]
)
df_3d["title"] = titles
df_3d["cluster"] = [str(c) for c in clusters]

# Create 3D scatter plot
fig = px.scatter_3d(
   df_3d,
   x='x',
   y='y',
   z='z',
   color='cluster',
   title='3D UMAP Visualization of Document Clusters',
   opacity=0.7,
   color_continuous_scale='viridis',
   size_max=0.5,
   hover_data=['title']  # Show title on hover
)

# Update layout
fig.update_layout(
   width=900,
   height=700,
   showlegend=True
)

fig.show()
