"""
Tree-sitter integration for AST parsing and node extraction (Python support first, extensible).
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import tree_sitter
import tree_sitter_python

from cig.graph_schema.nodes import BaseNode, ClassNode, FunctionNode, ModuleNode, NodeType, SourceSpan
from cig.parser.models import LoadedFile


def _get_node_text(node: tree_sitter.Node, code_bytes: bytes) -> str:
    return code_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _get_source_span(node: tree_sitter.Node) -> SourceSpan:
    return SourceSpan(
        start_line=node.start_point[0] + 1,
        start_column=node.start_point[1],
        end_line=node.end_point[0] + 1,
        end_column=node.end_point[1],
    )


def _clean_docstring(raw: str) -> str:
    s = raw.strip()
    for quote in ('"""', "'''", '"', "'"):
        if s.startswith(quote) and s.endswith(quote) and len(s) >= 2 * len(quote):
            s = s[len(quote) : -len(quote)]
            break
    return s.strip()


def _extract_docstring(block_or_module_node: tree_sitter.Node, code_bytes: bytes) -> Optional[str]:
    """Extract docstring from the first statement of a block or module if it is a string expression."""
    for child in block_or_module_node.children:
        if child.type in ("comment", "newline", "indent"):
            continue
        if child.type == "expression_statement":
            expr = child.children[0] if child.children else None
            if expr and expr.type in ("string", "concatenated_string"):
                return _clean_docstring(_get_node_text(expr, code_bytes))
        break
    return None


class PythonASTHandler:
    """Tree-sitter AST handler for Python language."""

    def __init__(self) -> None:
        self.language = tree_sitter.Language(tree_sitter_python.language())
        self.parser = tree_sitter.Parser(self.language)

    def file_path_to_module_path(self, file_path: str) -> Tuple[str, str]:
        """
        Convert file path to (module_name, module_path).
        e.g., 'mypackage/models.py' -> ('models', 'mypackage.models')
              'mypackage/__init__.py' -> ('mypackage', 'mypackage')
        """
        path = Path(file_path)
        parts = list(path.parts)

        # Remove extension from last part
        if parts:
            filename = parts[-1]
            if filename.endswith(".py"):
                filename = filename[:-3]
            parts[-1] = filename

        if len(parts) > 1 and parts[-1] == "__init__":
            parts.pop()

        module_path = ".".join(parts) if parts else "root"
        module_name = parts[-1] if parts else "root"
        return module_name, module_path

    def extract_parameters(self, params_node: tree_sitter.Node, code_bytes: bytes) -> List[str]:
        """Extract parameter names from python parameters AST node."""
        params: List[str] = []
        for child in params_node.children:
            if child.type in ("(", ")", ",", "*", "/"):
                continue
            if child.type == "identifier":
                params.append(_get_node_text(child, code_bytes))
            elif child.type in ("typed_parameter", "default_parameter", "typed_default_parameter"):
                for sub in child.children:
                    if sub.type == "identifier":
                        params.append(_get_node_text(sub, code_bytes))
                        break
            elif child.type in ("list_splat_pattern", "dictionary_splat_pattern"):
                for sub in child.children:
                    if sub.type == "identifier":
                        prefix = "*" if child.type == "list_splat_pattern" else "**"
                        params.append(prefix + _get_node_text(sub, code_bytes))
                        break
        return params

    def extract_nodes(self, loaded_file: LoadedFile) -> List[BaseNode]:
        code_bytes = loaded_file.content.encode("utf-8")
        tree = self.parser.parse(code_bytes)
        root = tree.root_node

        module_name, module_path = self.file_path_to_module_path(loaded_file.file_path)
        nodes: List[BaseNode] = []

        # 1. Extract ModuleNode
        module_docstring = _extract_docstring(root, code_bytes)
        module_node = ModuleNode(
            id=f"module:{module_path}",
            name=module_name,
            file_path=loaded_file.file_path,
            source_span=_get_source_span(root),
            docstring=module_docstring,
            module_path=module_path,
            imported_modules=[],
        )
        nodes.append(module_node)

        # 2. Extract Class and Function nodes recursively
        self._traverse_scope(root, module_path, parent_class_chain=[], code_bytes=code_bytes, nodes=nodes, loaded_file=loaded_file)

        return nodes

    def _traverse_scope(
        self,
        scope_node: tree_sitter.Node,
        module_path: str,
        parent_class_chain: List[str],
        code_bytes: bytes,
        nodes: List[BaseNode],
        loaded_file: LoadedFile,
    ) -> None:
        for child in scope_node.children:
            if child.type == "class_definition":
                self._extract_class(child, module_path, parent_class_chain, code_bytes, nodes, loaded_file)
            elif child.type in ("function_definition", "async_function_definition"):
                self._extract_function(child, module_path, parent_class_chain, code_bytes, nodes, loaded_file)
            elif child.type in ("block", "decorated_definition", "ERROR", "expression_statement"):
                self._traverse_scope(child, module_path, parent_class_chain, code_bytes, nodes, loaded_file)

    def _extract_class(
        self,
        class_node: tree_sitter.Node,
        module_path: str,
        parent_class_chain: List[str],
        code_bytes: bytes,
        nodes: List[BaseNode],
        loaded_file: LoadedFile,
    ) -> None:
        name_node = class_node.child_by_field_name("name")
        if not name_node:
            for c in class_node.children:
                if c.type == "identifier":
                    name_node = c
                    break
        if not name_node:
            return

        class_name = _get_node_text(name_node, code_bytes)
        current_chain = parent_class_chain + [class_name]
        class_id_str = ".".join(current_chain)
        class_id = f"class:{module_path}.{class_id_str}"

        # Superclasses / base classes
        base_classes: List[str] = []
        superclasses_node = class_node.child_by_field_name("superclasses")
        if superclasses_node:
            for arg in superclasses_node.children:
                if arg.type in ("identifier", "attribute"):
                    base_classes.append(_get_node_text(arg, code_bytes))

        # Docstring & Body
        body_node = class_node.child_by_field_name("body")
        docstring = _extract_docstring(body_node, code_bytes) if body_node else None

        # Pre-extract method IDs
        method_ids: List[str] = []
        if body_node:
            for child in body_node.children:
                func_child = child
                if child.type == "decorated_definition":
                    for sub in child.children:
                        if sub.type in ("function_definition", "async_function_definition"):
                            func_child = sub
                            break
                if func_child.type in ("function_definition", "async_function_definition"):
                    m_name_node = func_child.child_by_field_name("name")
                    if not m_name_node:
                        for sub in func_child.children:
                            if sub.type == "identifier":
                                m_name_node = sub
                                break
                    if m_name_node:
                        m_name = _get_node_text(m_name_node, code_bytes)
                        method_ids.append(f"func:{module_path}.{class_id_str}.{m_name}")

        cls_node = ClassNode(
            id=class_id,
            name=class_name,
            file_path=loaded_file.file_path,
            source_span=_get_source_span(class_node),
            docstring=docstring,
            base_classes=base_classes,
            methods=method_ids,
        )
        nodes.append(cls_node)

        # Traverse methods inside class body
        if body_node:
            self._traverse_scope(body_node, module_path, current_chain, code_bytes, nodes, loaded_file)

    def _extract_function(
        self,
        func_node: tree_sitter.Node,
        module_path: str,
        parent_class_chain: List[str],
        code_bytes: bytes,
        nodes: List[BaseNode],
        loaded_file: LoadedFile,
    ) -> None:
        is_async = (
            func_node.type == "async_function_definition"
            or any(c.type == "async" for c in func_node.children)
        )

        name_node = func_node.child_by_field_name("name")
        if not name_node:
            for c in func_node.children:
                if c.type == "identifier":
                    name_node = c
                    break
        if not name_node:
            return

        func_name = _get_node_text(name_node, code_bytes)
        if parent_class_chain:
            prefix = ".".join(parent_class_chain)
            func_id = f"func:{module_path}.{prefix}.{func_name}"
        else:
            func_id = f"func:{module_path}.{func_name}"

        # Parameters
        parameters: List[str] = []
        params_node = func_node.child_by_field_name("parameters")
        if params_node:
            parameters = self.extract_parameters(params_node, code_bytes)

        # Return type
        return_type: Optional[str] = None
        return_type_node = func_node.child_by_field_name("return_type")
        if return_type_node:
            return_type = _get_node_text(return_type_node, code_bytes)

        # Signature snippet
        body_node = func_node.child_by_field_name("body")
        if body_node:
            sig_bytes = code_bytes[func_node.start_byte : body_node.start_byte]
            signature = sig_bytes.decode("utf-8", errors="replace").strip().rstrip(":")
        else:
            signature = _get_node_text(func_node, code_bytes).split("\n")[0]

        # Docstring
        docstring = _extract_docstring(body_node, code_bytes) if body_node else None

        fn_node = FunctionNode(
            id=func_id,
            name=func_name,
            file_path=loaded_file.file_path,
            source_span=_get_source_span(func_node),
            docstring=docstring,
            signature=signature,
            parameters=parameters,
            return_type=return_type,
            is_async=is_async,
        )
        nodes.append(fn_node)


class ASTExtractor:
    """Language-extensible AST Extractor using tree-sitter parsers."""

    def __init__(self) -> None:
        self._handlers: Dict[str, PythonASTHandler] = {
            "python": PythonASTHandler()
        }

    def extract_nodes(self, loaded_file: LoadedFile) -> List[BaseNode]:
        """Extract AST nodes from a loaded file."""
        handler = self._handlers.get(loaded_file.language)
        if not handler:
            return []
        try:
            return handler.extract_nodes(loaded_file)
        except Exception:
            # Resilient to parsing crashes on unexpected files
            return []
