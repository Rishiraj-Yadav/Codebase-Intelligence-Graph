"""
Comprehensive test suite for Phase 2: Repository Ingestion and AST Extraction.
Tests repo loading, AST extraction (Python), edge extraction, deterministic IDs, and malformed input handling.
"""

import tempfile
from pathlib import Path
import pytest

from cig.graph_schema.nodes import NodeType, SourceSpan, FunctionNode, ClassNode, ModuleNode
from cig.graph_schema.edges import StructuralEdgeType, CallsEdge, ImportsEdge, InheritsEdge, InstantiatesEdge
from cig.parser.models import LoadedFile, ParsedRepository, ParseResult
from cig.parser.repo_loader import RepoLoader
from cig.parser.ast_extractor import ASTExtractor
from cig.parser.edge_extractor import EdgeExtractor
from cig.parser import parse_repository


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    """Creates a temporary sample repository structure with various Python files and ignore paths."""
    # Main package structure
    pkg = tmp_path / "mypackage"
    pkg.mkdir()
    (pkg / "__init__.py").write_text('"""My package docstring."""\n__version__ = "0.1.0"\n', encoding="utf-8")
    
    utils = pkg / "utils.py"
    utils.write_text(
        '"""Utility module."""\n'
        'import os\n'
        'from math import sqrt\n\n'
        'def helper(x: int) -> float:\n'
        '    """Helper function docstring."""\n'
        '    return sqrt(float(x))\n',
        encoding="utf-8"
    )

    models_file = pkg / "models.py"
    models_file.write_text(
        '"""Models module."""\n'
        'from mypackage.utils import helper\n\n'
        'class BaseEntity:\n'
        '    """Base entity docstring."""\n'
        '    def __init__(self, name: str):\n'
        '        self.name = name\n\n'
        'class User(BaseEntity):\n'
        '    """User entity docstring."""\n'
        '    def __init__(self, name: str, age: int):\n'
        '        super().__init__(name)\n'
        '        self.age = age\n\n'
        '    async def compute_score(self) -> float:\n'
        '        val = helper(self.age)\n'
        '        return val * 1.5\n\n'
        'def create_user() -> User:\n'
        '    u = User("Alice", 30)\n'
        '    return u\n',
        encoding="utf-8"
    )

    # Ignored directory & files
    pycache = pkg / "__pycache__"
    pycache.mkdir()
    (pycache / "cached.pyc").write_bytes(b"binary data")

    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "lib.py").write_text("def hidden(): pass\n", encoding="utf-8")

    return tmp_path


class TestRepoLoader:
    def test_repo_loader_file_enumeration(self, sample_repo: Path):
        loader = RepoLoader(repo_path=sample_repo)
        files = loader.load_files()

        rel_paths = [f.file_path for f in files]
        # Should be deterministically sorted relative paths using forward slashes
        assert rel_paths == sorted(rel_paths)
        assert "mypackage/__init__.py" in rel_paths
        assert "mypackage/models.py" in rel_paths
        assert "mypackage/utils.py" in rel_paths
        
        # Ignored dirs should not be included
        assert not any("__pycache__" in p for p in rel_paths)
        assert not any(".venv" in p for p in rel_paths)

    def test_language_detection(self, sample_repo: Path):
        loader = RepoLoader(repo_path=sample_repo)
        files = loader.load_files()
        for f in files:
            assert f.language == "python"

    def test_custom_ignore_patterns(self, sample_repo: Path):
        loader = RepoLoader(repo_path=sample_repo, ignore_patterns=["utils.py"])
        files = loader.load_files()
        rel_paths = [f.file_path for f in files]
        assert "mypackage/utils.py" not in rel_paths
        assert "mypackage/models.py" in rel_paths


class TestASTExtractor:
    def test_python_module_extraction(self):
        code = '"""Module docstring."""\nimport math\n'
        extractor = ASTExtractor()
        file_obj = LoadedFile(
            file_path="mypackage/foo.py",
            language="python",
            content=code,
            size_bytes=len(code)
        )
        nodes = extractor.extract_nodes(file_obj)

        module_nodes = [n for n in nodes if isinstance(n, ModuleNode)]
        assert len(module_nodes) == 1
        mod = module_nodes[0]
        assert mod.name == "foo"
        assert mod.module_path == "mypackage.foo"
        assert mod.docstring == "Module docstring."
        assert mod.id == "module:mypackage.foo"

    def test_python_function_extraction(self):
        code = (
            'async def fetch_data(url: str, timeout: int = 10) -> dict:\n'
            '    """Fetch data docstring."""\n'
            '    return {}\n'
        )
        extractor = ASTExtractor()
        file_obj = LoadedFile(
            file_path="mypackage/api.py",
            language="python",
            content=code,
            size_bytes=len(code)
        )
        nodes = extractor.extract_nodes(file_obj)

        func_nodes = [n for n in nodes if isinstance(n, FunctionNode)]
        assert len(func_nodes) == 1
        fn = func_nodes[0]
        assert fn.name == "fetch_data"
        assert fn.is_async is True
        assert "url" in fn.parameters
        assert "timeout" in fn.parameters
        assert fn.return_type == "dict"
        assert fn.docstring == "Fetch data docstring."
        assert fn.id == "func:mypackage.api.fetch_data"
        
        # Verify source span details (1-indexed lines)
        assert fn.source_span.start_line == 1
        assert fn.source_span.end_line == 3

    def test_python_class_extraction(self):
        code = (
            'class Animal(BaseModel, Entity):\n'
            '    """Animal class."""\n'
            '    def speak(self) -> str:\n'
            '        return "hello"\n'
        )
        extractor = ASTExtractor()
        file_obj = LoadedFile(
            file_path="mypackage/zoo.py",
            language="python",
            content=code,
            size_bytes=len(code)
        )
        nodes = extractor.extract_nodes(file_obj)

        class_nodes = [n for n in nodes if isinstance(n, ClassNode)]
        assert len(class_nodes) == 1
        cls = class_nodes[0]
        assert cls.name == "Animal"
        assert cls.base_classes == ["BaseModel", "Entity"]
        assert cls.docstring == "Animal class."
        assert cls.id == "class:mypackage.zoo.Animal"
        assert len(cls.methods) == 1
        assert cls.methods[0] == "func:mypackage.zoo.Animal.speak"

        func_nodes = [n for n in nodes if isinstance(n, FunctionNode)]
        assert len(func_nodes) == 1
        method = func_nodes[0]
        assert method.name == "speak"
        assert method.id == "func:mypackage.zoo.Animal.speak"


class TestEdgeExtractor:
    def test_edge_extraction_imports_inherits_calls_instantiates(self, sample_repo: Path):
        parse_result = parse_repository(sample_repo)
        
        edges = parse_result.edges
        edge_types = {e.edge_type for e in edges}
        assert StructuralEdgeType.IMPORTS in edge_types
        assert StructuralEdgeType.INHERITS in edge_types
        assert StructuralEdgeType.CALLS in edge_types
        assert StructuralEdgeType.INSTANTIATES in edge_types

        # Verify inherits edge User -> BaseEntity
        inherits_edges = [e for e in edges if e.edge_type == StructuralEdgeType.INHERITS]
        assert any(
            e.source_id == "class:mypackage.models.User" and "BaseEntity" in e.target_id
            for e in inherits_edges
        )

        # Verify instantiates edge create_user -> User
        inst_edges = [e for e in edges if e.edge_type == StructuralEdgeType.INSTANTIATES]
        assert any(
            e.source_id == "func:mypackage.models.create_user" and "User" in e.target_id
            for e in inst_edges
        )


class TestDeterminismAndMalformedInput:
    def test_deterministic_parsing(self, sample_repo: Path):
        res1 = parse_repository(sample_repo)
        res2 = parse_repository(sample_repo)

        assert [n.id for n in res1.nodes] == [n.id for n in res2.nodes]
        assert [e.id for e in res1.edges] == [e.id for e in res2.edges]

    def test_malformed_syntax_handling(self):
        bad_code = (
            "def broken_function(x, y):\n"
            "    val = x +\n"
            "\n"
            "class ValidClass:\n"
            "    def valid_method(self):\n"
            "        pass\n"
        )
        file_obj = LoadedFile(
            file_path="mypackage/bad.py",
            language="python",
            content=bad_code,
            size_bytes=len(bad_code)
        )
        extractor = ASTExtractor()
        nodes = extractor.extract_nodes(file_obj)
        
        # Extractor should not crash, and should extract ValidClass and valid_method as tree-sitter recovers
        class_names = [n.name for n in nodes if isinstance(n, ClassNode)]
        assert "ValidClass" in class_names

    def test_parsed_repository_query_helpers(self, sample_repo: Path):
        res = parse_repository(sample_repo)
        assert len(res.functions) > 0
        assert len(res.classes) > 0
        assert len(res.modules) > 0

        user_cls = res.get_node("class:mypackage.models.User")
        assert user_cls is not None
        assert user_cls.name == "User"

        edges_from = res.get_edges_from("class:mypackage.models.User")
        assert len(edges_from) > 0

        edges_to = res.get_edges_to(user_cls.id)
        assert len(edges_to) > 0

