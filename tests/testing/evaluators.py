from typing import Any, Callable, Union

from langchain.chat_models import init_chat_model
from openevals import create_llm_as_judge
from openevals.prompts.correctness import CORRECTNESS_PROMPT
from openevals.types import SimpleEvaluator


class LLMJudge:
    def __init__(
        self,
        *,
        model: str = "google_genai:gemini-2.0-flash-lite",
        temperature: float = 0.0,
    ):
        """Create a LLM as a judge using preset defaults.

        Args:
            model: Uses Gemini-2.0-flash-lite.

        Returns:
            A LLMJudge object that can create evaluators.
        """
        self.judge = init_chat_model(model=model, temperature=temperature)

    def create_correctness_evaluator(
        self,
        *,
        plaintext=False,
        continuous: bool = True,
        prompt: str = CORRECTNESS_PROMPT,
        **kwargs,
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
                judge=self.judge,
                **kwargs,
            )

            if plaintext:
                outputs_contents = outputs["output"]
                reference_outputs_contents = reference_outputs["message"]["content"]
            else:
                outputs_contents = outputs
                reference_outputs_contents = reference_outputs

            eval_result = evaluator(
                inputs=inputs,
                outputs=outputs_contents,
                reference_outputs=reference_outputs_contents,
            )
            return eval_result

        return correctness_evaluator


__all__ = [
    LLMJudge.__name__,
]
