"""
M5: DeBERTa Cross-Encoder Interface for Semantic Edge Labeling.
Determines semantic relationship labels between code node pairs.
"""

from typing import Optional, Tuple
from cig.graph_schema.contracts import M5SemanticEdgeLabelerOutput
from cig.models.mock_models import MockM5EdgeLabeler


class DeBERTaEdgeLabeler:
    """
    Inference interface for M5 (DeBERTa Semantic Edge Labeler).
    Classifies relationships between code snippets or node summaries.
    """

    def __init__(
        self,
        model_name_or_path: str = "microsoft/deberta-v3-base",
        peft_adapter_path: Optional[str] = None,
        device: Optional[str] = None,
        use_mock_fallback: bool = False,
    ):
        self.model_name_or_path = model_name_or_path
        self.peft_adapter_path = peft_adapter_path
        self.device = device
        self.use_mock_fallback = use_mock_fallback
        self._mock = MockM5EdgeLabeler()

        self.model = None
        self.tokenizer = None

        if not self.use_mock_fallback:
            self._load_model()

    def _load_model(self) -> None:
        """Loads HuggingFace DeBERTa cross-encoder with optional PEFT adapter."""
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name_or_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name_or_path)

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

    def predict(
        self,
        source_code: str,
        target_code: str,
        source_summary: Optional[str] = None,
        target_summary: Optional[str] = None,
    ) -> M5SemanticEdgeLabelerOutput:
        """Accepts two code snippets/summaries, returns M5SemanticEdgeLabelerOutput contract."""
        label, confidence, explanation, output = self.label_edge(
            source_code, target_code, source_summary, target_summary
        )
        return output

    def label_edge(
        self,
        source_code: str,
        target_code: str,
        source_summary: Optional[str] = None,
        target_summary: Optional[str] = None,
    ) -> Tuple[str, float, str, M5SemanticEdgeLabelerOutput]:
        """Accepts two function code/summaries, returns semantic label plus confidence plus explanation + M5SemanticEdgeLabelerOutput."""
        if self.use_mock_fallback or self.model is None or self.tokenizer is None:
            return self._mock.label_edge(
                source_code, target_code, source_summary, target_summary
            )

        try:
            import torch

            src_str = source_summary if source_summary else source_code[:256]
            tgt_str = target_summary if target_summary else target_code[:256]

            inputs = self.tokenizer(src_str, tgt_str, return_tensors="pt", max_length=512, truncation=True)
            if self.device:
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                logits = self.model(**inputs).logits
                probs = torch.softmax(logits, dim=-1)[0]
                pred_idx = torch.argmax(probs).item()
                confidence = float(probs[pred_idx].item())

            labels = ["CALLS", "DATA_FLOW", "DEPENDS_ON", "HELPER_OF", "SEMANTIC_SIMILARITY"]
            predicted_label = labels[pred_idx % len(labels)]
            explanation = f"Cross-encoder classified relation as {predicted_label} with confidence {confidence:.2f}."

            output_obj = M5SemanticEdgeLabelerOutput(
                semantic_label=predicted_label,
                confidence=round(confidence, 2),
                explanation=explanation,
            )
            return predicted_label, round(confidence, 2), explanation, output_obj
        except Exception:
            return self._mock.label_edge(
                source_code, target_code, source_summary, target_summary
            )
