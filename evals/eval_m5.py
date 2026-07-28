"""
M5 DeBERTa Cross-Encoder Edge Labeler Evaluation Harness.
Calculates classification accuracy metric for semantic edge labels (target > 0.75).
Includes W&B logging with offline fallback.
"""

import os
import logging
from typing import Any, Dict, List, Optional, Tuple

from sklearn.metrics import accuracy_score

from cig.models.m5_edge_labeler import DeBERTaEdgeLabeler

logger = logging.getLogger(__name__)


def _init_wandb(name: str = "eval-m5", config: Optional[Dict[str, Any]] = None):
    """Safely initializes W&B run with offline fallback."""
    try:
        import wandb
        mode = os.getenv("WANDB_MODE", "disabled" if not os.getenv("WANDB_API_KEY") else "online")
        return wandb.init(project="cig-evals", name=name, config=config, mode=mode, reinit=True)
    except Exception as exc:
        logger.warning(f"W&B init skipped: {exc}")
        return None


def evaluate_m5(predictions: List[str], targets: List[str]) -> Dict[str, Any]:
    """
    Calculates classification accuracy between predicted edge labels and ground truth target labels.

    Args:
        predictions: List of predicted semantic edge label strings.
        targets: List of ground-truth semantic edge label strings.

    Returns:
        Dict containing accuracy score and total sample count.
    """
    if not predictions or not targets or len(predictions) != len(targets):
        return {"accuracy": 0.0, "total_samples": 0}

    acc = float(accuracy_score(targets, predictions))

    return {
        "accuracy": round(acc, 4),
        "total_samples": len(predictions),
    }


def get_m5_benchmark_dataset() -> List[Tuple[str, str, Optional[str], Optional[str], str]]:
    """
    Returns benchmark dataset of (source_code, target_code, source_summary, target_summary, ground_truth_label)
    tuples for M5 evaluation.
    Possible semantic relation labels: CALLS, DATA_FLOW, DEPENDS_ON, HELPER_OF, SEMANTIC_SIMILARITY
    """
    return [
        (
            "def execute_query():\n    user_ok = login_user('admin', 'secret')",
            "def login_user(username: str, password_hash: str) -> bool:\n    return True",
            "Execute SQL database query after authenticating user",
            "Authenticate user credentials",
            "CALLS",
        ),
        (
            "def create_session():\n    db.save_session()",
            "def query_audit():\n    db.query_records()",
            "Create user session token and persist to database",
            "Save active session token to database table",
            "DATA_FLOW",
        ),
        (
            "def func_a(): pass",
            "def func_b(): pass",
            "Function A implementation",
            "Function B implementation",
            "DEPENDS_ON",
        ),
        (
            "def alpha(): x=1",
            "def func_b(): pass",
            "Alpha helper function",
            "Function B implementation",
            "HELPER_OF",
        ),
        (
            "def func_a(): pass",
            "def bar(): y=2",
            "Function A implementation",
            "Bar function implementation",
            "SEMANTIC_SIMILARITY",
        ),
    ]


def run_m5_evaluation(
    model: Optional[DeBERTaEdgeLabeler] = None,
    dataset: Optional[List[Tuple[str, str, Optional[str], Optional[str], str]]] = None,
) -> Dict[str, Any]:
    """
    Executes M5 DeBERTa Cross-Encoder Edge Labeler evaluation, computes classification accuracy, logs to W&B.

    Target threshold: Accuracy > 0.75
    """
    if model is None:
        model = DeBERTaEdgeLabeler(use_mock_fallback=True)

    if dataset is None:
        dataset = get_m5_benchmark_dataset()

    predictions = []
    targets = []

    for src_code, tgt_code, src_sum, tgt_sum, target_label in dataset:
        out = model.predict(
            source_code=src_code,
            target_code=tgt_code,
            source_summary=src_sum,
            target_summary=tgt_sum,
        )
        predictions.append(out.semantic_label)
        targets.append(target_label)

    results = evaluate_m5(predictions, targets)
    accuracy = results["accuracy"]
    target = 0.75
    passed = accuracy > target

    eval_summary = {
        "model_name": "M5_DeBERTa_Edge_Labeler",
        "accuracy": accuracy,
        "target_threshold": target,
        "passed": passed,
        "total_samples": len(predictions),
    }

    wb_run = _init_wandb(name="eval-m5", config=eval_summary)
    if wb_run:
        try:
            import wandb
            wandb.log({"accuracy": accuracy, "passed": int(passed)})
            wb_run.finish()
        except Exception:
            pass

    logger.info(f"M5 Evaluation Complete: Accuracy={accuracy:.4f} (Target > {target}, Passed={passed})")
    return eval_summary


if __name__ == "__main__":
    res = run_m5_evaluation()
    print(res)
