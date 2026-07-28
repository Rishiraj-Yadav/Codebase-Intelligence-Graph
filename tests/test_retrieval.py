"""
Unit tests for FAISS Retrieval and Node Embedder (Phase 5).
Tests vector normalization, FAISS indexing, persistence/loading, and top-k vector similarity search.
"""

import os
import tempfile
import numpy as np
import pytest

from cig.graph_schema.nodes import FunctionNode, ClassNode, ModuleNode, SourceSpan
from cig.retrieval.embedder import NodeEmbedder
from cig.retrieval.faiss_index import FAISSIndex


# Sample nodes for testing
@pytest.fixture
def sample_function_node():
    return FunctionNode(
        id="func_001",
        name="authenticate_user",
        file_path="auth/service.py",
        source_span=SourceSpan(start_line=1, start_column=0, end_line=10, end_column=20),
        signature="def authenticate_user(username: str, password_hash: str) -> bool",
        docstring="Authenticate user against database.",
        parameters=["username", "password_hash"],
        return_type="bool",
    )


@pytest.fixture
def sample_class_node():
    return ClassNode(
        id="class_001",
        name="UserManager",
        file_path="auth/manager.py",
        source_span=SourceSpan(start_line=1, start_column=0, end_line=50, end_column=0),
        docstring="Manager class for user lifecycle.",
        base_classes=["BaseManager"],
        methods=["authenticate_user", "create_user"],
    )


@pytest.fixture
def sample_module_node():
    return ModuleNode(
        id="mod_001",
        name="auth",
        file_path="auth/__init__.py",
        source_span=SourceSpan(start_line=1, start_column=0, end_line=100, end_column=0),
        docstring="Auth package initialization module.",
        module_path="auth",
        imported_modules=["os", "sys"],
    )


class TestNodeEmbedder:
    """Tests for NodeEmbedder class."""

    def test_mock_embed_code_shape_and_dtype(self):
        embedder = NodeEmbedder(use_mock_fallback=True, embedding_dim=768)
        vec = embedder.embed_code("def foo(): pass")

        assert isinstance(vec, np.ndarray)
        assert vec.dtype == np.float32
        assert vec.shape == (768,)

    def test_mock_embed_code_l2_normalization(self):
        embedder = NodeEmbedder(use_mock_fallback=True, embedding_dim=768)
        vec = embedder.embed_code("def foo(x): return x + 1")

        norm = np.linalg.norm(vec)
        assert norm == pytest.approx(1.0, abs=1e-5)

    def test_mock_embed_code_determinism(self):
        embedder = NodeEmbedder(use_mock_fallback=True, embedding_dim=768)
        code = "def authenticate(user, pwd): return True"

        vec1 = embedder.embed_code(code)
        vec2 = embedder.embed_code(code)

        np.testing.assert_array_almost_equal(vec1, vec2)

    def test_mock_embed_code_different_inputs(self):
        embedder = NodeEmbedder(use_mock_fallback=True, embedding_dim=768)
        vec1 = embedder.embed_code("def func_a(): pass")
        vec2 = embedder.embed_code("def func_b(): pass")

        assert not np.allclose(vec1, vec2)

    def test_mock_embed_code_edge_cases(self):
        embedder = NodeEmbedder(use_mock_fallback=True, embedding_dim=768)

        # Empty string
        vec_empty = embedder.embed_code("")
        assert vec_empty.shape == (768,)
        assert np.linalg.norm(vec_empty) == pytest.approx(1.0, abs=1e-5)

        # None input
        vec_none = embedder.embed_code(None)
        assert vec_none.shape == (768,)

        # Syntax error code
        vec_syntax = embedder.embed_code("def broken(: x +")
        assert vec_syntax.shape == (768,)
        assert np.linalg.norm(vec_syntax) == pytest.approx(1.0, abs=1e-5)

        # Long code input
        long_code = "x = 1\n" * 1000
        vec_long = embedder.embed_code(long_code)
        assert vec_long.shape == (768,)
        assert np.linalg.norm(vec_long) == pytest.approx(1.0, abs=1e-5)

    def test_embed_node(self, sample_function_node, sample_class_node, sample_module_node):
        embedder = NodeEmbedder(use_mock_fallback=True, embedding_dim=768)

        vec_func = embedder.embed_node(sample_function_node)
        vec_class = embedder.embed_node(sample_class_node)
        vec_mod = embedder.embed_node(sample_module_node)

        for vec in (vec_func, vec_class, vec_mod):
            assert isinstance(vec, np.ndarray)
            assert vec.dtype == np.float32
            assert vec.shape == (768,)
            assert np.linalg.norm(vec) == pytest.approx(1.0, abs=1e-5)

        # Verify deterministic node embedding
        vec_func_again = embedder.embed_node(sample_function_node)
        np.testing.assert_array_almost_equal(vec_func, vec_func_again)


class TestFAISSIndex:
    """Tests for FAISSIndex class."""

    def test_initial_state(self):
        index = FAISSIndex(dim=768)
        assert len(index) == 0

    def test_add_vectors_and_len(self):
        index = FAISSIndex(dim=768)
        embedder = NodeEmbedder(use_mock_fallback=True, embedding_dim=768)

        node_ids = ["node_1", "node_2", "node_3"]
        vectors = [embedder.embed_code(f"def func_{i}(): pass") for i in range(3)]

        index.add_vectors(node_ids, vectors)

        assert len(index) == 3
        assert index.id_to_node_id[0] == "node_1"
        assert index.id_to_node_id[1] == "node_2"
        assert index.id_to_node_id[2] == "node_3"
        assert index.node_id_to_id["node_1"] == 0
        assert index.node_id_to_id["node_2"] == 1
        assert index.node_id_to_id["node_3"] == 2

    def test_search_top_k_exact_match(self):
        index = FAISSIndex(dim=768)
        embedder = NodeEmbedder(use_mock_fallback=True, embedding_dim=768)

        v1 = embedder.embed_code("def login(): pass")
        v2 = embedder.embed_code("def logout(): pass")
        v3 = embedder.embed_code("def process_payment(): pass")

        index.add_vectors(["node_login", "node_logout", "node_payment"], [v1, v2, v3])

        # Query with exact v1 vector
        results = index.search(v1, top_k=2)

        assert len(results) == 2
        assert results[0]["node_id"] == "node_login"
        assert results[0]["score"] == pytest.approx(1.0, abs=1e-4)

    def test_search_empty_index(self):
        index = FAISSIndex(dim=768)
        query = np.zeros(768, dtype=np.float32)
        query[0] = 1.0

        results = index.search(query, top_k=5)
        assert results == []

    def test_persistence_save_and_load(self):
        index = FAISSIndex(dim=768)
        embedder = NodeEmbedder(use_mock_fallback=True, embedding_dim=768)

        node_ids = ["n1", "n2", "n3"]
        vectors = [embedder.embed_code(f"code snippet {i}") for i in range(3)]

        index.add_vectors(node_ids, vectors)

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test_faiss.index")
            index.save(file_path)

            assert os.path.exists(file_path)

            # Test classmethod loading
            loaded_index = FAISSIndex.load(file_path)
            assert len(loaded_index) == 3
            assert loaded_index.id_to_node_id == index.id_to_node_id
            assert loaded_index.node_id_to_id == index.node_id_to_id

            # Verify search results on loaded index match original
            query = vectors[1]
            orig_res = index.search(query, top_k=3)
            loaded_res = loaded_index.search(query, top_k=3)

            assert len(loaded_res) == len(orig_res)
            for r_orig, r_load in zip(orig_res, loaded_res):
                assert r_orig["node_id"] == r_load["node_id"]
                assert r_orig["score"] == pytest.approx(r_load["score"], abs=1e-5)

            # Test instance method loading
            new_index = FAISSIndex(dim=768)
            new_index.load(file_path)
            assert len(new_index) == 3
            assert new_index.id_to_node_id == index.id_to_node_id

    def test_clear(self):
        index = FAISSIndex(dim=768)
        embedder = NodeEmbedder(use_mock_fallback=True, embedding_dim=768)

        index.add_vectors(["n1"], [embedder.embed_code("code")])
        assert len(index) == 1

        index.clear()
        assert len(index) == 0
        assert len(index.id_to_node_id) == 0
        assert len(index.node_id_to_id) == 0
