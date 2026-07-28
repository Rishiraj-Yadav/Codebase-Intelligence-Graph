"""
Pydantic models for parser layer typed against cig.graph_schema contracts.
"""

from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field

from cig.graph_schema.nodes import BaseNode, ClassNode, FunctionNode, ModuleNode
from cig.graph_schema.edges import (
    CallsEdge,
    ImportsEdge,
    InheritsEdge,
    InstantiatesEdge,
    StructuralEdge,
)


class LoadedFile(BaseModel):
    """Represents a source file loaded from a repository."""

    file_path: str = Field(..., description="Relative file path using forward slashes.")
    absolute_path: Optional[str] = Field(None, description="Absolute file path on local filesystem.")
    language: str = Field("unknown", description="Detected programming language.")
    content: str = Field("", description="Raw source code content.")
    size_bytes: int = Field(0, description="Size of file in bytes.")


class ParseError(BaseModel):
    """Represents an error encountered during parsing a file or repository."""

    file_path: str = Field(..., description="File path where parse error occurred.")
    error_message: str = Field(..., description="Description of the parse error.")
    line_number: Optional[int] = Field(None, description="Optional line number of error.")


class ParsedRepository(BaseModel):
    """Result container for repository parsing containing extracted files, nodes, and edges."""

    repo_path: str = Field(..., description="Repository root directory path.")
    files: List[LoadedFile] = Field(default_factory=list, description="Loaded repository source files.")
    nodes: List[Union[FunctionNode, ClassNode, ModuleNode, BaseNode]] = Field(
        default_factory=list, description="Extracted AST symbol nodes."
    )
    edges: List[Union[CallsEdge, ImportsEdge, InheritsEdge, InstantiatesEdge, StructuralEdge]] = Field(
        default_factory=list, description="Extracted structural graph edges."
    )
    parse_errors: List[ParseError] = Field(
        default_factory=list, description="Parse warnings or syntax errors encountered."
    )

    @property
    def functions(self) -> List[FunctionNode]:
        """Returns all FunctionNode entities."""
        return [n for n in self.nodes if isinstance(n, FunctionNode)]

    @property
    def classes(self) -> List[ClassNode]:
        """Returns all ClassNode entities."""
        return [n for n in self.nodes if isinstance(n, ClassNode)]

    @property
    def modules(self) -> List[ModuleNode]:
        """Returns all ModuleNode entities."""
        return [n for n in self.nodes if isinstance(n, ModuleNode)]

    def get_node(self, node_id: str) -> Optional[BaseNode]:
        """Lookup node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_edges_from(self, source_id: str) -> List[StructuralEdge]:
        """Find all edges originating from source_id."""
        return [e for e in self.edges if e.source_id == source_id]

    def get_edges_to(self, target_id: str) -> List[StructuralEdge]:
        """Find all edges pointing to target_id."""
        return [e for e in self.edges if e.target_id == target_id]


# Alias for convenience
ParseResult = ParsedRepository
