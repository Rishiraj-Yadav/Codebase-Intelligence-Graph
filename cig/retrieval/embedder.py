"""
Node Embedder interface for generating dense vector embeddings using UniXcoder / CodeBERT.
Supports embed_code(code_str) and embed_node(node) with deterministic mock fallback.
"""

import hashlib
from typing import Optional
import numpy as np

from cig.graph_schema.nodes import BaseNode


class NodeEmbedder:
    """
    Generates dense vector embeddings (Float32 numpy arrays) for code snippets and graph nodes.
    Uses UniXcoder / CodeBERT (microsoft/unixcoder-base) by default.
    Includes deterministic fallback mode for offline testing.
    """

    def __init__(
        self,
        model_name_or_path: str = "microsoft/unixcoder-base",
        device: Optional[str] = None,
        use_mock_fallback: bool = False,
        embedding_dim: int = 768,
    ):
        self.model_name_or_path = model_name_or_path
        self.device = device
        self.use_mock_fallback = use_mock_fallback
        self.embedding_dim = embedding_dim

        self.model = None
        self.tokenizer = None

        if not self.use_mock_fallback:
            self._load_model()

    def _load_model(self) -> None:
        """Loads HuggingFace UniXcoder/CodeBERT model and tokenizer."""
        try:
            from transformers import AutoTokenizer, AutoModel

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name_or_path)
            self.model = AutoModel.from_pretrained(self.model_name_or_path)

            if self.device:
                self.model.to(self.device)
            self.model.eval()
        except Exception:
            # Fall back to mock mode on load failure or missing environment
            self.use_mock_fallback = True

    def embed_code(self, code_str: Optional[str]) -> np.ndarray:
        """
        Generates a dense, L2-normalized float32 vector embedding for a code string.

        Args:
            code_str: Source code snippet or text string.

        Returns:
            np.ndarray: 1D Float32 numpy array of shape (embedding_dim,).
        """
        if code_str is None:
            code_str = ""
        else:
            code_str = str(code_str)

        if self.use_mock_fallback or self.model is None or self.tokenizer is None:
            return self._mock_embed_code(code_str)

        try:
            import torch

            inputs = self.tokenizer(code_str, return_tensors="pt", max_length=512, truncation=True)
            if self.device:
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)

            # Mean pooling over token representations
            vec = outputs.last_hidden_state.mean(dim=1).squeeze(0).cpu().numpy().astype(np.float32)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            return vec
        except Exception:
            return self._mock_embed_code(code_str)

    def _mock_embed_code(self, code_str: str) -> np.ndarray:
        """Generates a fast, deterministic mock vector embedding for code_str."""
        digest = hashlib.sha256(code_str.encode("utf-8")).digest()
        seed = int.from_bytes(digest[:4], byteorder="big")
        rng = np.random.RandomState(seed)

        raw_vec = rng.randn(self.embedding_dim).astype(np.float32)
        norm = np.linalg.norm(raw_vec)
        if norm > 0:
            vec = raw_vec / norm
        else:
            vec = raw_vec
        return vec.astype(np.float32)

    def embed_node(self, node: BaseNode) -> np.ndarray:
        """
        Generates a dense vector embedding for an AST graph node.

        Args:
            node: BaseNode instance (FunctionNode, ClassNode, ModuleNode).

        Returns:
            np.ndarray: 1D Float32 numpy array of shape (embedding_dim,).
        """
        parts = [
            f"ID: {node.id}",
            f"Name: {node.name}",
            f"Type: {node.node_type}",
            f"File: {node.file_path}",
        ]

        if hasattr(node, "signature") and node.signature:
            parts.append(f"Signature: {node.signature}")

        if hasattr(node, "docstring") and node.docstring:
            parts.append(f"Docstring: {node.docstring}")

        if hasattr(node, "base_classes") and node.base_classes:
            parts.append(f"Bases: {', '.join(node.base_classes)}")

        if hasattr(node, "module_path") and node.module_path:
            parts.append(f"Module: {node.module_path}")

        if node.summary:
            parts.append(f"Summary: {node.summary}")

        text_representation = "\n".join(parts)
        return self.embed_code(text_representation)
