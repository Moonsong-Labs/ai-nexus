from typing import Any, Callable, Union

from openevals import create_llm_as_judge
from openevals.prompts.correctness import CORRECTNESS_PROMPT
from openevals.types import SimpleEvaluator


class LLMJudge:
    def __init__(
        self,
        *,
        model: str = "google_genai:gemini-2.0-flash-lite",
    ):
        """Create a LLM as a judge using preset defaults.

        Args:
            model: Uses Gemini-2.0-flash-lite.

        Returns:
            A LLMJudge object that can create evaluators.
        """
        self.model = model

    def create_correctness_evaluator(
        self, continuous: bool = True, prompt: str = CORRECTNESS_PROMPT, **kwargs
    ) -> Union[SimpleEvaluator, Callable[..., Any]]:
        """Create a correctness evaluator using preset defaults.

        Args:
            continuous: True.
            prompt: Uses CORRECTNESS_PROMPT.

        Returns:
            An evaluator function that takes inputs, outputs and reference_outputs.
        """

        def correctness_evaluator(inputs: dict, outputs: dict, reference_outputs: dict):
            evaluator = create_llm_as_judge(
                prompt=prompt,
                continuous=continuous,
                model=self.model,
                **kwargs,
            )

            eval_result = evaluator(
                inputs=inputs,
                outputs=outputs,
                reference_outputs=reference_outputs,
            )
            return eval_result

        return correctness_evaluator


__all__ = [
    LLMJudge.__name__,
]
