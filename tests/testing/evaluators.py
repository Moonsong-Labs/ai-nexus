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
        self.model = model

    def create_correctness_evaluator(
        self, continuous: bool = True, prompt: str = CORRECTNESS_PROMPT, **kwargs
    ) -> Union[SimpleEvaluator, Callable[..., Any]]:
        """Create a LLM as a judge evaluator using preset defaults.

        Args:
            continuous: True.
            prompt: Uses CORRECTNESS_PROMPT.
            model: Uses Gemini-2.0-flash-lite.

        Returns:
            A function with the
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


# def correctness_evaluator(inputs: dict, outputs: dict, reference_outputs: dict):
#     evaluator = create_correctness_judge()
#     outputs_contents = outputs["output"]
#     reference_outputs_contents = reference_outputs["message"]["content"]

#     eval_result = evaluator(
#         inputs=inputs,
#         outputs=outputs_contents,
#         reference_outputs=reference_outputs_contents,
#     )
#     return eval_result


# def create_correctness_judge(
#     *,
#     continuous: bool = True,
#     prompt: str = CORRECTNESS_PROMPT,
#     model: str = "google_genai:gemini-2.0-flash-lite",
#     **kwargs,
# ):
#     """Create a LLM as a judge using preset defaults.

#     Args:
#         continuous: True.
#         prompt: Uses CORRECTNESS_PROMPT.
#         model: Uses Gemini-2.0-flash-lite.
#     """
#     return create_llm_as_judge(
#         prompt=prompt,
#         continuous=continuous,
#         model=model,
#         **kwargs,
#     )


__all__ = [
    LLMJudge.__name__,
]
