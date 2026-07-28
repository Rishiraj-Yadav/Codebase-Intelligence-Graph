"""
Extraction of structural edges (CallsEdge, ImportsEdge, InheritsEdge, InstantiatesEdge) from AST.
"""

from typing import Dict, List, Optional, Set, Tuple, Union
import tree_sitter
import tree_sitter_python

from cig.graph_schema.nodes import BaseNode, ClassNode, FunctionNode, ModuleNode, SourceSpan
from cig.graph_schema.edges import (
    CallsEdge,
    ImportsEdge,
    InheritsEdge,
    InstantiatesEdge,
    StructuralEdge,
)
from cig.parser.models import LoadedFile


def _get_node_text(node: tree_sitter.Node, code_bytes: bytes) -> str:
    return code_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


class EdgeExtractor:
    """Extracts structural graph edges from parsed AST nodes and file sources."""

    def __init__(self) -> None:
        self.language = tree_sitter.Language(tree_sitter_python.language())
        self.parser = tree_sitter.Parser(self.language)

    def extract_edges(
        self, files: List[LoadedFile], nodes: List[BaseNode]
    ) -> List[StructuralEdge]:
        """
        Extract structural edges from files and extracted AST nodes.
        Returns a deterministically sorted list of StructuralEdge instances.
        """
        edges: List[StructuralEdge] = []
        
        # Build symbol table indexes for resolution
        class_by_name: Dict[str, ClassNode] = {}
        func_by_name: Dict[str, FunctionNode] = {}
        node_by_id: Dict[str, BaseNode] = {}

        for node in nodes:
            node_by_id[node.id] = node
            if isinstance(node, ClassNode):
                class_by_name[node.name] = node
            elif isinstance(node, FunctionNode):
                func_by_name[node.name] = node

        # 1. Inherits edges
        for node in nodes:
            if isinstance(node, ClassNode):
                for base in node.base_classes:
                    target_id = class_by_name[base].id if base in class_by_name else f"class:{base}"
                    edge_id = f"edge:inherits:{node.id}->{target_id}"
                    edges.append(
                        InheritsEdge(
                            id=edge_id,
                            source_id=node.id,
                            target_id=target_id,
                        )
                    )

        # 2. Imports, Calls, and Instantiates edges from file ASTs
        file_map = {f.file_path: f for f in files}

        for node in nodes:
            if isinstance(node, ModuleNode):
                loaded_file = file_map.get(node.file_path)
                if not loaded_file or loaded_file.language != "python":
                    continue
                
                code_bytes = loaded_file.content.encode("utf-8")
                tree = self.parser.parse(code_bytes)

                # Extract imports
                self._extract_imports(tree.root_node, node, code_bytes, edges)

                # Extract calls & instantiations
                module_funcs = [n for n in nodes if isinstance(n, FunctionNode) and n.file_path == node.file_path]
                self._extract_calls(tree.root_node, node, module_funcs, class_by_name, func_by_name, code_bytes, edges)

        # Sort and deduplicate edges deterministically
        unique_edges: Dict[str, StructuralEdge] = {}
        for edge in edges:
            if edge.id not in unique_edges:
                unique_edges[edge.id] = edge

        sorted_edges = sorted(
            unique_edges.values(),
            key=lambda e: (e.edge_type.value, e.source_id, e.target_id, e.id),
        )
        return sorted_edges

    def _extract_imports(
        self,
        root: tree_sitter.Node,
        module_node: ModuleNode,
        code_bytes: bytes,
        edges: List[StructuralEdge],
    ) -> None:
        """Extract import statements into ImportsEdge instances and populate module_node.imported_modules."""
        imported_set: Set[str] = set()

        def _traverse(node: tree_sitter.Node):
            if node.type == "import_statement":
                for child in node.children:
                    if child.type == "dotted_name":
                        mod_name = _get_node_text(child, code_bytes)
                        imported_set.add(mod_name)
                        target_id = f"module:{mod_name}"
                        edge_id = f"edge:imports:{module_node.id}->{target_id}"
                        edges.append(
                            ImportsEdge(
                                id=edge_id,
                                source_id=module_node.id,
                                target_id=target_id,
                            )
                        )
                    elif child.type == "aliased_import":
                        dname = child.child_by_field_name("name")
                        if dname:
                            mod_name = _get_node_text(dname, code_bytes)
                            imported_set.add(mod_name)
                            target_id = f"module:{mod_name}"
                            edge_id = f"edge:imports:{module_node.id}->{target_id}"
                            edges.append(
                                ImportsEdge(
                                    id=edge_id,
                                    source_id=module_node.id,
                                    target_id=target_id,
                                )
                            )
            elif node.type == "import_from_statement":
                mod_name = ""
                for child in node.children:
                    if child.type in ("dotted_name", "relative_import"):
                        mod_name = _get_node_text(child, code_bytes)
                        imported_set.add(mod_name)
                        break
                if mod_name:
                    target_id = f"module:{mod_name}"
                    edge_id = f"edge:imports:{module_node.id}->{target_id}"
                    edges.append(
                        ImportsEdge(
                            id=edge_id,
                            source_id=module_node.id,
                            target_id=target_id,
                        )
                    )

            for child in node.children:
                _traverse(child)

        _traverse(root)
        module_node.imported_modules = sorted(list(imported_set))

    def _extract_calls(
        self,
        root: tree_sitter.Node,
        module_node: ModuleNode,
        functions: List[FunctionNode],
        class_by_name: Dict[str, ClassNode],
        func_by_name: Dict[str, FunctionNode],
        code_bytes: bytes,
        edges: List[StructuralEdge],
    ) -> None:
        """Extract call invocations and instantiations."""
        def _get_enclosing_func_id(start_line: int, end_line: int) -> str:
            for fn in functions:
                if fn.source_span.start_line <= start_line and fn.source_span.end_line >= end_line:
                    return fn.id
            return module_node.id

        def _traverse(node: tree_sitter.Node):
            if node.type == "call":
                fn_child = node.children[0] if node.children else None
                if fn_child:
                    callee_name = ""
                    if fn_child.type == "identifier":
                        callee_name = _get_node_text(fn_child, code_bytes)
                    elif fn_child.type == "attribute":
                        attr_name = fn_child.child_by_field_name("attribute")
                        if attr_name:
                            callee_name = _get_node_text(attr_name, code_bytes)
                        else:
                            callee_name = _get_node_text(fn_child, code_bytes)

                    if callee_name and callee_name not in ("print", "len", "super", "range", "str", "int", "float", "list", "dict", "set"):
                        start_line = node.start_point[0] + 1
                        end_line = node.end_point[0] + 1
                        source_id = _get_enclosing_func_id(start_line, end_line)

                        # Check if callee is a class instantiation
                        if callee_name in class_by_name:
                            target_id = class_by_name[callee_name].id
                            edge_id = f"edge:instantiates:{source_id}->{target_id}:{start_line}"
                            edges.append(
                                InstantiatesEdge(
                                    id=edge_id,
                                    source_id=source_id,
                                    target_id=target_id,
                                )
                            )
                        else:
                            # Calls edge
                            target_id = func_by_name[callee_name].id if callee_name in func_by_name else f"func:{callee_name}"
                            edge_id = f"edge:calls:{source_id}->{target_id}:{start_line}"
                            edges.append(
                                CallsEdge(
                                    id=edge_id,
                                    source_id=source_id,
                                    target_id=target_id,
                                )
                            )

            for child in node.children:
                _traverse(child)

        _traverse(root)
