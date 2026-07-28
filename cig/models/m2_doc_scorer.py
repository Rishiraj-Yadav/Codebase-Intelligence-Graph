"""
M2: CodeBERT Doc Scorer Interface for Docstring Quality Assessment.
Evaluates code documentation quality, assigning scores and identifying docstring issues.
"""

from typing import List, Optional, Tuple
from cig.graph_schema.contracts import M2DocScorerOutput
from cig.models.mock_models import MockM2DocScorer


class CodeBERTDocScorer:
    """
    Inference interface for M2 (CodeBERT Doc Scorer).
    Evaluates quality of docstrings against code implementation.
    """

    def __init__(
        self,
        model_name_or_path: str = "microsoft/codebert-base",
        peft_adapter_path: Optional[str] = None,
        device: Optional[str] = None,
        use_mock_fallback: bool = False,
    ):
        self.model_name_or_path = model_name_or_path
        self.peft_adapter_path = peft_adapter_path
        self.device = device
        self.use_mock_fallback = use_mock_fallback
        self._mock = MockM2DocScorer()

        self.model = None
        self.tokenizer = None

        if not self.use_mock_fallback:
            self._load_model()

    def _load_model(self) -> None:
        """Loads HuggingFace CodeBERT model and tokenizer with optional PEFT adapter."""
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name_or_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name_or_path, num_labels=1
            )

            if self.peft_adapter_path:
                try:
                    from peft import PeftModel

                    self.model = PeftModel.from_pretrained(self.model, self.peft_adapter_path)
                except ImportError:
                    pass

            if self.device:
                self.model.to(self.device)
            self.model.eval()
        except Exception:
            self.use_mock_fallback = True

    def predict(self, code: str, docstring: Optional[str] = None) -> M2DocScorerOutput:
        """Accepts code and optional docstring, returns M2DocScorerOutput contract."""
        score_100, issues, output = self.score_docstring(code, docstring)
        return output

    def score_docstring(
        self, code: str, docstring: Optional[str] = None
    ) -> Tuple[float, List[str], M2DocScorerOutput]:
        """Accepts code + docstring, returns score 0-100 plus issues list + M2DocScorerOutput."""
        if self.use_mock_fallback or self.model is None or self.tokenizer is None:
            return self._mock.score_docstring(code, docstring)

        try:
            import torch

            text_input = f"{docstring or ''} </s> {code}"
            inputs = self.tokenizer(text_input, return_tensors="pt", max_length=512, truncation=True)
            if self.device:
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                logits = self.model(**inputs).logits
                raw_score = torch.sigmoid(logits).item()

            quality_score = round(float(raw_score), 2)
            score_100 = round(quality_score * 100.0, 2)
            issues: List[str] = []

            if not docstring or not docstring.strip():
                issues.append("Docstring is missing.")
                feedback = "Add a docstring explaining parameters and return values."
            elif quality_score < 0.6:
                issues.append("Low docstring coverage or detail.")
                feedback = "Expand docstring details."
            else:
                feedback = "Good docstring quality."

            output_obj = M2DocScorerOutput(
                doc_quality_score=quality_score,
                doc_feedback=feedback,
                confidence=0.88,
            )
            return score_100, issues, output_obj
        except Exception:
            return self._mock.score_docstring(code, docstring)
