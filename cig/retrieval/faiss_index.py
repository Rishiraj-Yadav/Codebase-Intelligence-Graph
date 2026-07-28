"""
FAISS Index wrapper for vector indexing and similarity search.
Uses faiss.IndexFlatIP with L2-normalized embeddings and maintains integer ID <-> node_id mappings.
"""

import json
import os
from typing import Any, Dict, List, Union, Optional
import faiss
import numpy as np


class _LoadMethod:
    """Descriptor supporting both FAISSIndex.load(path) and index.load(path)."""

    def __get__(self, instance, owner=None):
        if instance is None:
            def class_load(file_path: str) -> "FAISSIndex":
                idx = owner()
                return idx._load_impl(file_path)
            return class_load
        else:
            def instance_load(file_path: str) -> "FAISSIndex":
                return instance._load_impl(file_path)
            return instance_load


class FAISSIndex:
    """
    FAISS Index Flat Inner Product wrapper for fast dense vector retrieval.
    Maintains a bi-directional mapping between FAISS integer IDs and string node_ids.
    """

    load = _LoadMethod()

    def __init__(self, dim: int = 768):
        self.dim = dim
        self.index = faiss.IndexFlatIP(self.dim)
        self.id_to_node_id: Dict[int, str] = {}
        self.node_id_to_id: Dict[str, int] = {}
        self._next_id: int = 0

    def add_vectors(
        self,
        node_ids: List[str],
        vectors: Union[np.ndarray, List[np.ndarray]],
    ) -> None:
        """
        Adds vectors to the FAISS index and associates them with node_ids.

        Args:
            node_ids: List of string node IDs.
            vectors: 2D numpy array of shape (N, dim) or list of 1D numpy arrays.
        """
        if isinstance(vectors, list):
            vecs_arr = np.array(vectors, dtype=np.float32)
        else:
            vecs_arr = np.asarray(vectors, dtype=np.float32)

        if vecs_arr.ndim == 1:
            vecs_arr = np.expand_dims(vecs_arr, axis=0)

        if vecs_arr.shape[1] != self.dim:
            raise ValueError(f"Vector dimension {vecs_arr.shape[1]} does not match index dimension {self.dim}")

        if len(node_ids) != vecs_arr.shape[0]:
            raise ValueError(f"Mismatch between number of node_ids ({len(node_ids)}) and vectors ({vecs_arr.shape[0]})")

        # L2-normalize vectors for Inner Product search
        norms = np.linalg.norm(vecs_arr, axis=1, keepdims=True)
        vecs_arr = vecs_arr / np.maximum(norms, 1e-12)
        vecs_arr = np.ascontiguousarray(vecs_arr, dtype=np.float32)

        start_id = self._next_id
        for i, node_id in enumerate(node_ids):
            int_id = start_id + i
            self.id_to_node_id[int_id] = node_id
            self.node_id_to_id[node_id] = int_id

        self._next_id += len(node_ids)
        self.index.add(vecs_arr)

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Searches the FAISS index for the top_k most similar vectors to query_vector.

        Args:
            query_vector: 1D or 2D numpy float32 vector.
            top_k: Number of nearest neighbors to return.

        Returns:
            List[Dict[str, Any]]: List of dicts with 'node_id' and 'score'.
        """
        if len(self) == 0:
            return []

        q_arr = np.asarray(query_vector, dtype=np.float32)
        if q_arr.ndim == 1:
            q_arr = np.expand_dims(q_arr, axis=0)

        # L2 normalize query vector
        norm = np.linalg.norm(q_arr, axis=1, keepdims=True)
        q_arr = q_arr / np.maximum(norm, 1e-12)
        q_arr = np.ascontiguousarray(q_arr, dtype=np.float32)

        k = min(top_k, len(self))
        scores, indices = self.index.search(q_arr, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            int_idx = int(idx)
            if int_idx != -1 and int_idx in self.id_to_node_id:
                results.append(
                    {
                        "node_id": self.id_to_node_id[int_idx],
                        "score": float(score),
                    }
                )

        return results

    def save(self, file_path: str) -> None:
        """
        Saves the FAISS index and metadata mappings to disk.

        Args:
            file_path: Output file path for index binary.
        """
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        faiss.write_index(self.index, str(file_path))

        meta_path = f"{file_path}.meta.json"
        metadata = {
            "dim": self.dim,
            "next_id": self._next_id,
            "id_to_node_id": {str(k): v for k, v in self.id_to_node_id.items()},
            "node_id_to_id": self.node_id_to_id,
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    def _load_impl(self, file_path: str) -> "FAISSIndex":
        """Internal loader method."""
        meta_path = f"{file_path}.meta.json"
        if not os.path.exists(meta_path):
            meta_path_alt = f"{file_path}.meta"
            if os.path.exists(meta_path_alt):
                meta_path = meta_path_alt

        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        self.dim = metadata.get("dim", 768)
        self._next_id = metadata.get("next_id", 0)
        self.id_to_node_id = {int(k): v for k, v in metadata.get("id_to_node_id", {}).items()}
        self.node_id_to_id = metadata.get("node_id_to_id", {})

        self.index = faiss.read_index(str(file_path))
        return self

    def clear(self) -> None:
        """Clears vectors and mappings from the index."""
        self.index = faiss.IndexFlatIP(self.dim)
        self.id_to_node_id.clear()
        self.node_id_to_id.clear()
        self._next_id = 0

    def __len__(self) -> int:
        return self.index.ntotal
