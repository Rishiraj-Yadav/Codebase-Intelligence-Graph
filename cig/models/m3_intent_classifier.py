"""
M3: CodeBERT Multi-label Intent Classifier Interface.
Classifies code snippets across 15 semantic intent taxonomies.
"""

from typing import Dict, List, Optional, Tuple
from cig.graph_schema.contracts import (
    M3IntentClassifierOutput,
    IntentCategory,
    INTENT_TAXONOMY,
)
from cig.models.mock_models import MockM3IntentClassifier


class CodeBERTIntentClassifier:
    """
    Inference interface for M3 (CodeBERT Multi-Label Intent Classifier).
    Categorizes code intents across 15 intent categories.
    """

    def __init__(
        self,
        model_name_or_path: str = "microsoft/codebert-base",
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
        self._mock = MockM3IntentClassifier(threshold=threshold)

        self.model = None
        self.tokenizer = None

        if not self.use_mock_fallback:
            self._load_model()

    def _load_model(self) -> None:
        """Loads HuggingFace CodeBERT multi-label classifier with optional PEFT adapter."""
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name_or_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name_or_path, num_labels=len(INTENT_TAXONOMY)
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

    def predict(self, code: str) -> M3IntentClassifierOutput:
        """Accepts code string, returns M3IntentClassifierOutput contract."""
        intents, probs, output = self.classify(code)
        return output

    def classify(
        self, code: str
    ) -> Tuple[List[IntentCategory], Dict[str, float], M3IntentClassifierOutput]:
        """Accepts module/function code, returns intent label list with probabilities + M3IntentClassifierOutput."""
        if self.use_mock_fallback or self.model is None or self.tokenizer is None:
            return self._mock.classify(code)

        try:
            import torch

            inputs = self.tokenizer(code, return_tensors="pt", max_length=512, truncation=True)
            if self.device:
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                logits = self.model(**inputs).logits
                probs_tensor = torch.sigmoid(logits)[0]

            label_probs: Dict[str, float] = {}
            intents: List[IntentCategory] = []

            for idx, cat_str in enumerate(INTENT_TAXONOMY):
                prob = float(probs_tensor[idx].item())
                label_probs[cat_str] = round(prob, 2)
                if prob >= self.threshold:
                    intents.append(IntentCategory(cat_str))

            overall_conf = round(max(label_probs.values()) if label_probs else 0.0, 2)
            output_obj = M3IntentClassifierOutput(
                intent_labels=intents,
                label_probabilities=label_probs,
                confidence=overall_conf,
            )
            return intents, label_probs, output_obj
        except Exception:
            return self._mock.classify(code)
