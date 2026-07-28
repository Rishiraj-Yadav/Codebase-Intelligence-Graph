"""
M1: CodeT5 Model Interface for Code Summarization.
Converts source code snippets into concise natural language summaries.
"""

from typing import Optional, Tuple
from cig.graph_schema.contracts import M1CodeSummarizerOutput
from cig.models.mock_models import MockM1Summarizer


class CodeT5Summarizer:
    """
    Inference interface for M1 (CodeT5 Code Summarizer).
    Supports PEFT/LoRA adapters and fallback to deterministic mock.
    """

    def __init__(
        self,
        model_name_or_path: str = "Salesforce/codet5-base",
        peft_adapter_path: Optional[str] = None,
        device: Optional[str] = None,
        use_mock_fallback: bool = False,
    ):
        self.model_name_or_path = model_name_or_path
        self.peft_adapter_path = peft_adapter_path
        self.device = device
        self.use_mock_fallback = use_mock_fallback
        self._mock = MockM1Summarizer()

        self.model = None
        self.tokenizer = None

        if not self.use_mock_fallback:
            self._load_model()

    def _load_model(self) -> None:
        """Loads HuggingFace CodeT5 model and tokenizer with optional PEFT adapter."""
        try:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name_or_path)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name_or_path)

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
            # On loading failure or missing packages/weights, enable mock fallback
            self.use_mock_fallback = True

    def predict(self, code: str) -> M1CodeSummarizerOutput:
        """Accepts code string, returns M1CodeSummarizerOutput contract."""
        summary, output = self.summarize(code)
        return output

    def summarize(self, code: str) -> Tuple[str, M1CodeSummarizerOutput]:
        """Accepts function code, returns summary string + M1CodeSummarizerOutput."""
        if self.use_mock_fallback or self.model is None or self.tokenizer is None:
            return self._mock.summarize(code)

        try:
            import torch

            inputs = self.tokenizer(code, return_tensors="pt", max_length=512, truncation=True)
            if self.device:
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model.generate(**inputs, max_new_tokens=64, return_dict_in_generate=True, output_scores=True)

            summary = self.tokenizer.decode(outputs.sequences[0], skip_special_tokens=True)
            # Estimate confidence from sequence probability if scores available
            confidence = 0.85
            if hasattr(outputs, "sequences_scores") and outputs.sequences_scores is not None:
                confidence = float(torch.exp(outputs.sequences_scores[0]).item())
                confidence = max(0.0, min(1.0, confidence))

            output_obj = M1CodeSummarizerOutput(
                summary=summary,
                confidence=round(confidence, 2),
            )
            return summary, output_obj
        except Exception:
            return self._mock.summarize(code)
