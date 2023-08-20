import logging
from typing import List

from app.base_types import CacheItem
from app.core.data_processors.openai.openai import OpenAI
from app.core.data_processors.openai.openai_utils import OpenAIChatCompletion, OpenAIRoles, OpenAIModels


class DuplicatesRemover:
    # todo: setup logging to local file

    def __init__(self, openai: OpenAI):
        self._openai = openai
        self._system_message = OpenAIChatCompletion(
            role=OpenAIRoles.SYSTEM,
            content=(
                "You are an editor for a newsletter. The user will send articles one by one. For each article,"
                " returns 1 if the article is sufficiently different from the articles before it in order for it to be"
                " included in the newsletter, and 0 otherwise."
            ),
        )

    async def remove_duplicated_articles(self, items: List[CacheItem]) -> List[CacheItem]:
        non_duplicated_items = []
        messages = [self._system_message]

        for item in items:
            messages.append(OpenAIChatCompletion(role=OpenAIRoles.USER, content=item.article.content))
            completion = await self._openai.get_chat_completions(model=OpenAIModels.GPT_3_5_TURBO, messages=messages)
            if int(completion.content) == 1:
                non_duplicated_items.append(item)
            messages.append(completion)

        return non_duplicated_items

    @staticmethod
    def _get_invalid_indices(completion: OpenAIChatCompletion) -> List[int]:
        completion_content = completion.content
        try:
            invalid_indices = [int(completion_index) for completion_index in completion_content.split(" ")]
        except Exception:
            logging.getLogger(__name__).error(f"Invalid completion: {completion_content}")
            invalid_indices = []
        return invalid_indices
