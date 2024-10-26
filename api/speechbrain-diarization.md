# speechbrain.processing.diarization

Key functions:

- `read_rttm(rttm_file_path)`: Reads an RTTM file and returns contents as a list.

- `write_ders_file(ref_rttm, DER, out_der_file)`: Writes DER results to a file.

- `prepare_subset_csv(full_diary_csv, rec_id, out_csv_file)`: Prepares CSV for a specific recording ID.

- `is_overlapped(end1, start2)`: Checks if two segments overlap.

- `merge_ssegs_same_speaker(lol)`: Merges adjacent segments from same speaker.

- `distribute_overlap(lol)`: Distributes overlapped speech among adjacent segments.

- `write_rttm(segs_list, out_rttm_file)`: Writes segments to RTTM file.

- `get_oracle_num_spkrs(rec_id, spkr_info)`: Gets actual number of speakers from ground truth.

- `spectral_embedding_sb(adjacency, n_components=8, norm_laplacian=True, drop_first=True)`: Computes spectral embeddings.

- `spectral_clustering_sb(affinity, n_clusters=8, n_components=None, random_state=None, n_init=10)`: Performs spectral clustering.

- `do_spec_clustering(diary_obj, out_rttm_file, rec_id, k, pval, affinity_type, n_neighbors)`: Performs spectral clustering on embeddings.

- `do_kmeans_clustering(diary_obj, out_rttm_file, rec_id, k_oracle=4, p_val=0.3)`: Performs k-means clustering on embeddings. 

- `do_AHC(diary_obj, out_rttm_file, rec_id, k_oracle=4, p_val=0.3)`: Performs agglomerative hierarchical clustering on embeddings.

Key classes:

- `Spec_Cluster`: Performs spectral clustering using sklearn.

- `Spec_Clust_unorm`: Implements spectral clustering with unnormalized affinity matrix.
  Methods:
  - `do_spec_clust(X, k_oracle, p_val)`: Main spectral clustering function.
  - `get_sim_mat(X)`: Computes similarity matrix.
  - `p_pruning(A, pval)`: Prunes affinity matrix.
  - `get_laplacian(M)`: Computes Laplacian matrix.
  - `get_spec_embs(L, k_oracle=4)`: Gets spectral embeddings.
  - `cluster_embs(emb, k)`: Clusters embeddings using k-means.
