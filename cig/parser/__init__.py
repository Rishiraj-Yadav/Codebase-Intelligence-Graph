"""
CIG Parser Package: Repository Ingestion and AST Extraction.
"""

from pathlib import Path
from typing import List, Optional, Union

from cig.parser.ast_extractor import ASTExtractor
from cig.parser.edge_extractor import EdgeExtractor
from cig.parser.models import LoadedFile, ParseError, ParsedRepository, ParseResult
from cig.parser.repo_loader import RepoLoader


def parse_repository(
    repo_path: Union[str, Path],
    ignore_patterns: Optional[List[str]] = None,
) -> ParsedRepository:
    """
    Main entrypoint to parse a repository:
    1. Traverses repository and loads source files.
    2. Extracts AST symbol nodes (Modules, Classes, Functions).
    3. Extracts structural edges (Imports, Inherits, Calls, Instantiates).

    Returns a typed ParsedRepository / ParseResult container.
    """
    repo_path_obj = Path(repo_path).resolve()
    loader = RepoLoader(repo_path=repo_path_obj, ignore_patterns=ignore_patterns)
    files = loader.load_files()

    ast_extractor = ASTExtractor()
    edge_extractor = EdgeExtractor()

    all_nodes = []
    parse_errors = []

    for file_obj in files:
        try:
            nodes = ast_extractor.extract_nodes(file_obj)
            all_nodes.extend(nodes)
        except Exception as e:
            parse_errors.append(
                ParseError(
                    file_path=file_obj.file_path,
                    error_message=str(e),
                )
            )

    all_edges = edge_extractor.extract_edges(files, all_nodes)

    return ParsedRepository(
        repo_path=str(repo_path_obj),
        files=files,
        nodes=all_nodes,
        edges=all_edges,
        parse_errors=parse_errors,
    )


__all__ = [
    "RepoLoader",
    "ASTExtractor",
    "EdgeExtractor",
    "parse_repository",
    "LoadedFile",
    "ParsedRepository",
    "ParseResult",
    "ParseError",
]
