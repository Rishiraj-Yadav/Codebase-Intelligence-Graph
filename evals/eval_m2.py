"""
M2 CodeBERT Doc Scorer Evaluation Harness.
Calculates Spearman rank correlation evaluation metric for docstring quality (target > 0.65).
Includes W&B logging with offline fallback.
"""

import os
import logging
from typing import Any, Dict, List, Optional, Tuple

import scipy.stats as stats

from cig.models.m2_doc_scorer import CodeBERTDocScorer

logger = logging.getLogger(__name__)


def _init_wandb(name: str = "eval-m2", config: Optional[Dict[str, Any]] = None):
    """Safely initializes W&B run with offline fallback."""
    try:
        import wandb
        mode = os.getenv("WANDB_MODE", "disabled" if not os.getenv("WANDB_API_KEY") else "online")
        return wandb.init(project="cig-evals", name=name, config=config, mode=mode, reinit=True)
    except Exception as exc:
        logger.warning(f"W&B init skipped: {exc}")
        return None


def evaluate_m2(predictions: List[float], targets: List[float]) -> Dict[str, Any]:
    """
    Calculates Spearman rank correlation coefficient between predicted doc quality scores and ground truth targets.

    Args:
        predictions: List of predicted docstring quality scores (0.0 to 1.0 or 0 to 100).
        targets: List of ground-truth quality scores.

    Returns:
        Dict containing spearman_correlation (-1.0 to 1.0) and p_value.
    """
    if not predictions or not targets or len(predictions) != len(targets):
        return {"spearman_correlation": 0.0, "p_value": 1.0, "total_samples": 0}

    rho, p_val = stats.spearmanr(predictions, targets)
    if not isinstance(rho, float) and hasattr(rho, "item"):
        rho = float(rho)
    if not isinstance(p_val, float) and hasattr(p_val, "item"):
        p_val = float(p_val)

    if str(rho) == "nan":
        rho = 0.0

    return {
        "spearman_correlation": round(float(rho), 4),
        "p_value": round(float(p_val), 4),
        "total_samples": len(predictions),
    }


def get_m2_benchmark_dataset() -> List[Tuple[str, Optional[str], float]]:
    """
    Returns benchmark dataset of (code, docstring, ground_truth_score) tuples for M2 evaluation.
    Ground truth quality score ranges from 0.0 to 1.0.
    """
    return [
        (
            "def login_user(username: str, password_hash: str) -> bool:\n    return True",
            "Authenticate user with username and password hash. Returns boolean status.",
            0.92,
        ),
        (
            "def execute_query(query_str: str) -> list:\n    return []",
            "Execute SQL query string and return list of row results.",
            0.88,
        ),
        (
            "def process_data(data: list) -> list:\n    return [x * 2 for x in data]",
            "Process data list.",
            0.70,
        ),
        (
            "def calc(x, y):\n    return x + y",
            "",  # missing docstring
            0.20,
        ),
        (
            "def auth(u, p):\n    pass",
            "auth",
            0.35,
        ),
        (
            "def get_user_session(user_id: str) -> Session:\n    return Session(user_id)",
            "Retrieve active session object for user ID with parameters and returns.",
            0.95,
        ),
        (
            "def parse_config(path: str) -> dict:\n    return {}",
            "Parses JSON configuration file from path. Returns dictionary of parameters.",
            0.90,
        ),
        (
            "def helper():\n    pass",
            None,
            0.20,
        ),
        (
            "def compute_metrics(matrix: list) -> dict:\n    return {}",
            "Computes standard evaluation metrics from confusion matrix.",
            0.85,
        ),
        (
            "def validate_input(val):\n    if not val: raise ValueError()",
            "Validates input value. Raises ValueError if invalid.",
            0.86,
        ),
    ]


def run_m2_evaluation(
    model: Optional[CodeBERTDocScorer] = None,
    dataset: Optional[List[Tuple[str, Optional[str], float]]] = None,
) -> Dict[str, Any]:
    """
    Executes M2 CodeBERT Doc Scorer evaluation, computes Spearman rank correlation, logs to W&B.

    Target threshold: Spearman Rank Correlation > 0.65
    """
    if model is None:
        model = CodeBERTDocScorer(use_mock_fallback=True)

    if dataset is None:
        dataset = get_m2_benchmark_dataset()

    predictions = []
    targets = []

    for code, docstring, target_score in dataset:
        out = model.predict(code, docstring)
        predictions.append(out.doc_quality_score)
        targets.append(target_score)

    results = evaluate_m2(predictions, targets)
    spearman_corr = results["spearman_correlation"]
    target = 0.65
    passed = spearman_corr > target

    eval_summary = {
        "model_name": "M2_CodeBERT_Doc_Scorer",
        "spearman_correlation": spearman_corr,
        "p_value": results["p_value"],
        "target_threshold": target,
        "passed": passed,
        "total_samples": len(predictions),
    }

    wb_run = _init_wandb(name="eval-m2", config=eval_summary)
    if wb_run:
        try:
            import wandb
            wandb.log({"spearman_correlation": spearman_corr, "passed": int(passed)})
            wb_run.finish()
        except Exception:
            pass

    logger.info(
        f"M2 Evaluation Complete: Spearman Correlation={spearman_corr:.4f} (Target > {target}, Passed={passed})"
    )
    return eval_summary


if __name__ == "__main__":
    res = run_m2_evaluation()
    print(res)
