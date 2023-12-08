from pydantic import validator

from app.base_types import Config
from app.core.data_processors.openai.openai_utils import OpenAIModels
from app.db.session import SessionLocal
from app import crud


class NewsletterCreatorConfig(Config):
    version: int = 0
    summary_prompt: str = (
        "You are an editor for a newsletter that summarizes articles in up to {word_count} words."
        " The user will provide you with an article and you will reply with the summary and only"
        " the summary. The summary itself should be in an article form and will be included in a newsletter"
        " as a shorter version of the full article. Feel free to break the summary into easily digestible paragraphs."
    )
    summary_max_word_count: int = 350
    min_description_len_for_evaluation_prompts: int = 200
    article_redundancy_prompt: str = (
        "You are a newsletter editor curating articles for a newsletter. Based on the following article summaries,"
        " is the information in the two articles redundant or covering the same event or topic?"
        "\n\nThe first article is:\n\n{previous_article_summary}"
        "\n\nThe second article summary is:\n\n{current_article_summary}\n\nOnly reply with yes or no."
    )
    article_relevancy_prompt: str = (
        "You are a newsletter editor curating articles for a custom newsletter for a particular customer."
        " The newsletter is in english. The customer's description of the newsletter they want is the following:"
        "\n\n{newsletter_description}"
        "\n\nBased on the description, would you include the following article in the newsletter:"
        "\n\n{current_article_summary}\n\nOnly reply with yes or no."
    )
    articles_qualifier_prompt: str = (
        "You are a newsletter curator for my personal newsletter. Here is my description of the newsletter:"
        " \"{newsletter_description}\" I will give you {articles_count} articles. I want you to tell me which,"
        " if any, of the articles you would include in the next issue of the newsletter based on relevancy."
        " Also, I want you to tell me which, if any, of the articles are mutually redundant—in other words,"
        " which articles cover the same topics/events."
        "\n\nYour response will be in JSON format. For example, if articles 1, 2 and 3 are relevant,"
        " and articles 2 and 3 and 4 and 5 have redundant information, your reply will be:"
        "\n\n{{"
        "\n    \"include\": [1, 2, 3],"
        "\n    \"redundant\": [[2, 3], [4, 5]]"
        "\n}}"
        "\n\nThis JSON will be your only response, nothing else."
        "\n\nHere are the articles:"
    )
    newsletter_subject_prompt: str = (
        "You are a newsletter editor curating articles for a newsletter. Your task is to come up with an email"
        " subject for the latest newsletter email. I will provide you with the content of the newsletter and you"
        " have to reply with the newsletter subject line. I only want the subject line and nothing else. The subject"
        " line should not be enclosed in quotes. Here is the content of the newsletter:\n\n{newsletter_content}"
    )
    max_articles_per_newsletter: int = 5
    max_processed_articles_per_newsletter: int = 7
    text_generation_model: OpenAIModels = OpenAIModels.GPT_4_TURBO
    decision_model: OpenAIModels = OpenAIModels.GPT_4_TURBO

    @validator("min_description_len_for_evaluation_prompts")
    def must_be_smaller_than_summary_max_word_count(
        cls, v, values, **kwargs
    ):
        if v > values["summary_max_word_count"]:
            raise ValueError(
                "min_description_len_for_evaluation_prompts must be smaller than summary_max_word_count"
            )
        return v

    @validator("max_articles_per_newsletter")
    def max_articles_per_newsletter_must_be_greater_than_zero(cls, v, values, **kwargs):
        if v <= 0:
            raise ValueError("max_articles_per_newsletter must be greater than zero")
        return v

    @validator("max_processed_articles_per_newsletter")
    def max_processed_articles_per_newsletter_must_be_greater_than_max_articles_per_newsletter(
        cls, v, values, **kwargs
    ):
        if "max_articles_per_newsletter" in values and v < values["max_articles_per_newsletter"]:
            raise ValueError(
                "max_processed_articles_per_newsletter must be greater than or equal to max_articles_per_newsletter"
            )
        return v


def get_newsletter_generation_config_version_from_db() -> int:
    db = None
    try:
        db = SessionLocal()
        newsletter_generation_config = crud.newsletter_generation_config.get_by_config(
            db=db, config_in=newsletter_creator_config
        )
        if newsletter_generation_config is None:
            newsletter_generation_config = crud.newsletter_generation_config.create(
                db=db, obj_in=newsletter_creator_config
            )
    finally:
        db is not None and db.close()
    return newsletter_generation_config.id


newsletter_creator_config = NewsletterCreatorConfig()
newsletter_creator_config.version = get_newsletter_generation_config_version_from_db()


if __name__ == "__main__":
    print(f"config_version: {newsletter_creator_config.version}")
