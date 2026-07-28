"""
Test suite for Phase 8: Evaluation and Regression Harnesses.
Asserts evaluation scripts (M1-M5) metric computations against targets:
- M1 CodeT5 Summarizer BLEU-4 > 18.0
- M2 CodeBERT Doc Scorer Spearman Correlation > 0.65
- M3 CodeBERT Intent Classifier Macro F1 > 0.72 across 15 intent categories
- M4 GraphCodeBERT Smell Detector Per-class AUC-ROC > 0.80 across 5 smell categories
- M5 DeBERTa Edge Labeler Classification Accuracy > 0.75
- Pipeline Smoke Test end-to-end execution asserting all 5 annotations on graph entities.
"""

import os
import tempfile
from pathlib import Path
import pytest

from evals.eval_m1 import evaluate_m1, run_m1_evaluation
from evals.eval_m2 import evaluate_m2, run_m2_evaluation
from evals.eval_m3 import evaluate_m3, run_m3_evaluation
from evals.eval_m4 import evaluate_m4, run_m4_evaluation
from evals.eval_m5 import evaluate_m5, run_m5_evaluation
from evals.pipeline_smoke_test import run_pipeline_smoke_test


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    """Creates a temporary sample repository for pipeline smoke test."""
    pkg = tmp_path / "smoke_app"
    pkg.mkdir()
    (pkg / "__init__.py").write_text('"""App init."""\n', encoding="utf-8")

    auth = pkg / "auth.py"
    auth.write_text(
        '"""User authentication module."""\n'
        'def login_user(username: str, password_hash: str) -> bool:\n'
        '    """Authenticate user credentials."""\n'
        '    if not username or not password_hash:\n'
        '        return False\n'
        '    return True\n',
        encoding="utf-8"
    )

    db = pkg / "database.py"
    db.write_text(
        '"""Database connection module."""\n'
        'from smoke_app.auth import login_user\n\n'
        'def run_query(query_str: str) -> list:\n'
        '    """Run SQL query if authenticated."""\n'
        '    ok = login_user("admin", "pass")\n'
        '    if not ok:\n'
        '        raise PermissionError()\n'
        '    return [1, 2, 3]\n',
        encoding="utf-8"
    )
    return tmp_path


class TestM1SummarizerEval:
    def test_evaluate_m1_metric(self):
        preds = [
            "Authenticate user with username and password",
            "Execute SQL query against database session",
            "Calculate total price with tax and discount",
        ]
        refs = [
            "Authenticate user credentials with username and password",
            "Execute SQL database query",
            "Calculate item total price including tax and discount",
        ]
        res = evaluate_m1(preds, refs)
        assert isinstance(res, dict)
        assert "bleu_4" in res
        assert res["bleu_4"] >= 0.0

    def test_run_m1_evaluation_target(self):
        res = run_m1_evaluation()
        assert isinstance(res, dict)
        assert "bleu_4" in res
        assert res["bleu_4"] > 18.0, f"M1 BLEU-4 target > 18.0 failed: {res['bleu_4']}"


class TestM2DocScorerEval:
    def test_evaluate_m2_metric(self):
        preds = [0.85, 0.40, 0.90, 0.20, 0.75, 0.60]
        targets = [0.80, 0.35, 0.95, 0.15, 0.70, 0.65]
        res = evaluate_m2(preds, targets)
        assert isinstance(res, dict)
        assert "spearman_correlation" in res
        assert -1.0 <= res["spearman_correlation"] <= 1.0

    def test_run_m2_evaluation_target(self):
        res = run_m2_evaluation()
        assert isinstance(res, dict)
        assert "spearman_correlation" in res
        assert (
            res["spearman_correlation"] > 0.65
        ), f"M2 Spearman target > 0.65 failed: {res['spearman_correlation']}"


class TestM3IntentClassifierEval:
    def test_evaluate_m3_metric(self):
        # 15 intent categories binary vector predictions / targets
        num_samples = 20
        num_classes = 15
        import numpy as np
        y_true = np.zeros((num_samples, num_classes), dtype=int)
        y_pred = np.zeros((num_samples, num_classes), dtype=int)
        for i in range(num_samples):
            c = i % num_classes
            y_true[i, c] = 1
            y_pred[i, c] = 1
        res = evaluate_m3(y_pred, y_true)
        assert isinstance(res, dict)
        assert "macro_f1" in res
        assert 0.0 <= res["macro_f1"] <= 1.0

    def test_run_m3_evaluation_target(self):
        res = run_m3_evaluation()
        assert isinstance(res, dict)
        assert "macro_f1" in res
        assert res["num_categories"] == 15
        assert (
            res["macro_f1"] > 0.72
        ), f"M3 Macro F1 target > 0.72 failed: {res['macro_f1']}"


class TestM4SmellDetectorEval:
    def test_evaluate_m4_metric(self):
        import numpy as np
        num_samples = 20
        num_classes = 5
        y_true = np.zeros((num_samples, num_classes), dtype=int)
        y_scores = np.random.uniform(0, 1, (num_samples, num_classes))
        for i in range(num_samples):
            c = i % num_classes
            y_true[i, c] = 1
            y_scores[i, c] = 0.9  # high score for true class

        res = evaluate_m4(y_scores, y_true)
        assert isinstance(res, dict)
        assert "mean_auc_roc" in res
        assert "per_class_auc_roc" in res
        assert len(res["per_class_auc_roc"]) == 5

    def test_run_m4_evaluation_target(self):
        res = run_m4_evaluation()
        assert isinstance(res, dict)
        assert "mean_auc_roc" in res
        assert res["num_categories"] == 5
        assert (
            res["mean_auc_roc"] > 0.80
        ), f"M4 Mean AUC-ROC target > 0.80 failed: {res['mean_auc_roc']}"
        for cat, auc in res["per_class_auc_roc"].items():
            assert auc > 0.70, f"Smell class {cat} AUC low: {auc}"


class TestM5EdgeLabelerEval:
    def test_evaluate_m5_metric(self):
        preds = ["CALLS", "DATA_FLOW", "DEPENDS_ON", "HELPER_OF", "SEMANTIC_SIMILARITY"]
        targets = ["CALLS", "DATA_FLOW", "DEPENDS_ON", "HELPER_OF", "SEMANTIC_SIMILARITY"]
        res = evaluate_m5(preds, targets)
        assert isinstance(res, dict)
        assert "accuracy" in res
        assert res["accuracy"] == 1.0

    def test_run_m5_evaluation_target(self):
        res = run_m5_evaluation()
        assert isinstance(res, dict)
        assert "accuracy" in res
        assert (
            res["accuracy"] > 0.75
        ), f"M5 Accuracy target > 0.75 failed: {res['accuracy']}"


class TestPipelineSmokeTest:
    def test_end_to_end_pipeline_smoke_test(self, sample_repo: Path):
        with tempfile.TemporaryDirectory() as tmp_dir:
            faiss_path = os.path.join(tmp_dir, "smoke.index")
            res = run_pipeline_smoke_test(repo_path=sample_repo, faiss_index_path=faiss_path)

            assert isinstance(res, dict)
            assert res["status"] == "SUCCESS"
            assert res["nodes_count"] > 0
            assert res["edges_count"] > 0
            assert res["faiss_index_size"] == res["nodes_count"]

            # Assert all 5 annotations are verified
            annotations = res["verified_annotations"]
            assert annotations["m1_summary"] is True
            assert annotations["m2_doc_quality_score"] is True
            assert annotations["m3_intent_labels"] is True
            assert annotations["m4_smell_labels"] is True
            assert annotations["m5_semantic_label"] is True
