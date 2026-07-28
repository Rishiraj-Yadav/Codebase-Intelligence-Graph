"""
M3 CodeBERT Multi-Label Intent Classifier Evaluation Harness.
Calculates Macro F1 score across 15 intent categories (target > 0.72).
Includes W&B logging with offline fallback.
"""

import os
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.metrics import f1_score

from cig.graph_schema.contracts import INTENT_TAXONOMY, IntentCategory
from cig.models.m3_intent_classifier import CodeBERTIntentClassifier

logger = logging.getLogger(__name__)


def _init_wandb(name: str = "eval-m3", config: Optional[Dict[str, Any]] = None):
    """Safely initializes W&B run with offline fallback."""
    try:
        import wandb
        mode = os.getenv("WANDB_MODE", "disabled" if not os.getenv("WANDB_API_KEY") else "online")
        return wandb.init(project="cig-evals", name=name, config=config, mode=mode, reinit=True)
    except Exception as exc:
        logger.warning(f"W&B init skipped: {exc}")
        return None


def evaluate_m3(y_pred: Any, y_true: Any) -> Dict[str, Any]:
    """
    Calculates Macro F1 score across 15 intent categories using sklearn f1_score.

    Args:
        y_pred: Binary matrix/array of shape (N, 15) for predictions.
        y_true: Binary matrix/array of shape (N, 15) for ground truth targets.

    Returns:
        Dict containing macro_f1 score and category count.
    """
    y_pred_arr = np.array(y_pred)
    y_true_arr = np.array(y_true)

    if y_pred_arr.size == 0 or y_true_arr.size == 0:
        return {"macro_f1": 0.0, "num_categories": len(INTENT_TAXONOMY)}

    macro_f1 = f1_score(y_true_arr, y_pred_arr, average="macro", zero_division=0)

    return {
        "macro_f1": round(float(macro_f1), 4),
        "num_categories": y_true_arr.shape[1] if len(y_true_arr.shape) > 1 else len(INTENT_TAXONOMY),
        "total_samples": len(y_true_arr),
    }


def get_m3_benchmark_dataset() -> List[Tuple[str, List[str]]]:
    """
    Returns benchmark dataset of (code, ground_truth_intent_list) tuples across 15 intent categories.
    """
    return [
        (
            "def login_user(username: str, password_hash: str) -> bool:\n    if not username: return False\n    return True",
            [IntentCategory.AUTHENTICATION.value],
        ),
        (
            "def execute_sql_query(query: str) -> list:\n    session = db.get_session()\n    return session.execute(query)",
            [IntentCategory.DATABASE.value],
        ),
        (
            "def process_data_records(records: list) -> list:\n    return [transform(r) for r in records]",
            [IntentCategory.DATA_PROCESSING.value],
        ),
        (
            "def test_login_flow():\n    assert login_user('admin', 'hash') is True",
            [IntentCategory.TESTING.value],
        ),
        (
            "def fetch_api_endpoint(url: str) -> dict:\n    resp = requests.get(url)\n    return resp.json()",
            [IntentCategory.API_COMMUNICATION.value],
        ),
        (
            "def safe_divide(a: float, b: float) -> float:\n    try:\n        return a / b\n    except ZeroDivisionError:\n        raise ValueError('Cannot divide by zero')",
            [IntentCategory.ERROR_HANDLING.value],
        ),
        (
            "def write_output_file(path: str, content: str):\n    with open(path, 'w') as f:\n        f.write(content)",
            [IntentCategory.FILE_IO.value],
        ),
        (
            "def log_system_event(msg: str):\n    logger.info(f'EVENT: {msg}')",
            [IntentCategory.LOGGING.value],
        ),
        (
            "def render_dashboard_component(state: dict):\n    return f'<div>{state}</div>'",
            [IntentCategory.UI_RENDERING.value],
        ),
        (
            "def load_app_config(config_path: str) -> dict:\n    return json.load(open(config_path))",
            [IntentCategory.CONFIGURATION.value],
        ),
        (
            "def get_cached_item(key: str):\n    return cache.get(key)",
            [IntentCategory.CACHING.value],
        ),
        (
            "def train_model(X, y):\n    model = RandomForestClassifier()\n    return model.fit(X, y)",
            [IntentCategory.MACHINE_LEARNING.value],
        ),
        (
            "def send_message_to_queue(queue_name: str, payload: dict):\n    mq.send(queue_name, payload)",
            [IntentCategory.MESSAGING.value],
        ),
        (
            "def helper_slugify(name: str) -> str:\n    return name.lower().replace(' ', '-')",
            [IntentCategory.UTILITY.value],
        ),
        (
            "def apply_business_rule_price_discount(price: float, discount: float) -> float:\n    return price * (1.0 - discount)",
            [IntentCategory.BUSINESS_LOGIC.value],
        ),
    ]


def run_m3_evaluation(
    model: Optional[CodeBERTIntentClassifier] = None,
    dataset: Optional[List[Tuple[str, List[str]]]] = None,
) -> Dict[str, Any]:
    """
    Executes M3 CodeBERT Intent Classifier evaluation, computes Macro F1 metric across 15 categories, logs to W&B.

    Target threshold: Macro F1 > 0.72
    """
    if model is None:
        model = CodeBERTIntentClassifier(use_mock_fallback=True)

    if dataset is None:
        dataset = get_m3_benchmark_dataset()

    y_pred_list = []
    y_true_list = []

    for code, ground_truth_intents in dataset:
        out = model.predict(code)
        pred_intents = [label.value if hasattr(label, "value") else str(label) for label in out.intent_labels]

        # Construct binary vectors for 15 intent categories
        pred_vec = [1 if cat in pred_intents else 0 for cat in INTENT_TAXONOMY]
        true_vec = [1 if cat in ground_truth_intents else 0 for cat in INTENT_TAXONOMY]

        y_pred_list.append(pred_vec)
        y_true_list.append(true_vec)

    results = evaluate_m3(y_pred_list, y_true_list)
    macro_f1 = results["macro_f1"]
    target = 0.72
    passed = macro_f1 > target

    eval_summary = {
        "model_name": "M3_CodeBERT_Intent_Classifier",
        "macro_f1": macro_f1,
        "num_categories": len(INTENT_TAXONOMY),
        "target_threshold": target,
        "passed": passed,
        "total_samples": len(dataset),
    }

    wb_run = _init_wandb(name="eval-m3", config=eval_summary)
    if wb_run:
        try:
            import wandb
            wandb.log({"macro_f1": macro_f1, "passed": int(passed)})
            wb_run.finish()
        except Exception:
            pass

    logger.info(
        f"M3 Evaluation Complete: Macro F1={macro_f1:.4f} across 15 categories (Target > {target}, Passed={passed})"
    )
    return eval_summary


if __name__ == "__main__":
    res = run_m3_evaluation()
    print(res)
