"""
Evaluation Harness and Metric Verification Package for Codebase Intelligence Graph (CIG).
"""

from evals.eval_m1 import evaluate_m1, run_m1_evaluation
from evals.eval_m2 import evaluate_m2, run_m2_evaluation
from evals.eval_m3 import evaluate_m3, run_m3_evaluation
from evals.eval_m4 import evaluate_m4, run_m4_evaluation
from evals.eval_m5 import evaluate_m5, run_m5_evaluation
from evals.pipeline_smoke_test import run_pipeline_smoke_test

__all__ = [
    "evaluate_m1",
    "run_m1_evaluation",
    "evaluate_m2",
    "run_m2_evaluation",
    "evaluate_m3",
    "run_m3_evaluation",
    "evaluate_m4",
    "run_m4_evaluation",
    "evaluate_m5",
    "run_m5_evaluation",
    "run_pipeline_smoke_test",
]
