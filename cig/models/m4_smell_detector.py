"""
M4: GraphCodeBERT Code Smell Detector Interface.
Detects architectural and quality code smells across 5 smell categories.
"""

from typing import Dict, List, Optional, Tuple
from cig.graph_schema.contracts import (
    M4SmellDetectorOutput,
    SmellCategory,
    SMELL_TAXONOMY,
)
from cig.models.mock_models import MockM4SmellDetector


class GraphCodeBERTSmellDetector:
    """
    Inference interface for M4 (GraphCodeBERT Code Smell Detector).
    Identifies 5 code smell categories from source code.
    """

    def __init__(
        self,
        model_name_or_path: str = "microsoft/graphcodebert-base",
        peft_adapter_path: Optional[str] = None,
        device: Optional[str] = None,
        threshold: float = 0.5,
        use_mock_fallback: bool = False,
    ):
        self.model_name_or_path = model_name_or_path
        self.peft_adapter_path = peft_adapter_path
        self.device = device
        self.threshold = threshold
        self.use_mock_fallback = use_mock_fallback
        self._mock = MockM4SmellDetector(threshold=threshold)

        self.model = None
        self.tokenizer = None

        if not self.use_mock_fallback:
            self._load_model()

    def _load_model(self) -> None:
        """Loads HuggingFace GraphCodeBERT multi-label model with optional PEFT adapter."""
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name_or_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name_or_path, num_labels=len(SMELL_TAXONOMY)
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

    def predict(self, code: str) -> M4SmellDetectorOutput:
        """Accepts code string, returns M4SmellDetectorOutput contract."""
        probs, output = self.detect_smells(code)
        return output

    def detect_smells(
        self, code: str
    ) -> Tuple[Dict[str, float], M4SmellDetectorOutput]:
        """Accepts function code, returns per-smell probability dict + M4SmellDetectorOutput."""
        if self.use_mock_fallback or self.model is None or self.tokenizer is None:
            return self._mock.detect_smells(code)

        try:
            import torch

            inputs = self.tokenizer(code, return_tensors="pt", max_length=512, truncation=True)
            if self.device:
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                logits = self.model(**inputs).logits
                probs_tensor = torch.sigmoid(logits)[0]

            smell_probs: Dict[str, float] = {}
            detected_smells: List[SmellCategory] = []

            for idx, smell_str in enumerate(SMELL_TAXONOMY):
                prob = float(probs_tensor[idx].item())
                smell_probs[smell_str] = round(prob, 2)
                if prob >= self.threshold:
                    detected_smells.append(SmellCategory(smell_str))

            overall_conf = round(max(smell_probs.values()) if smell_probs else 0.0, 2)
            output_obj = M4SmellDetectorOutput(
                smell_labels=detected_smells,
                smell_probabilities=smell_probs,
                confidence=overall_conf,
            )
            return smell_probs, output_obj
        except Exception:
            return self._mock.detect_smells(code)
