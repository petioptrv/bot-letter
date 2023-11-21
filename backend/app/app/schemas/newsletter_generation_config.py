from pydantic import BaseModel


class NewsletterGenerationConfigBase(BaseModel):
    pass


class NewsletterGenerationConfigCreate(NewsletterGenerationConfigBase):
    summary_prompt: str
    summary_max_word_count: int
    min_article_description_to_consider_for_article_evaluation_prompts_instead_of_article_summary: int
    article_redundancy_prompt: str
    article_relevancy_prompt: str
    newsletter_subject_prompt: str
    max_articles_per_newsletter: int
    max_processed_articles_per_newsletter: int


class NewsletterGenerationConfigUpdate(NewsletterGenerationConfigBase):
    pass


class NewsletterGenerationConfigDelete(NewsletterGenerationConfigBase):
    id: int


class NewsletterGenerationConfigInDB(NewsletterGenerationConfigBase):
    id: int
    summary_prompt: str
    summary_max_word_count: int
    min_article_description_to_consider_for_article_evaluation_prompts_instead_of_article_summary: int
    article_redundancy_prompt: str
    article_relevancy_prompt: str
    newsletter_subject_prompt: str
    max_articles_per_newsletter: int
    max_processed_articles_per_newsletter: int

    class Config:
        orm_mode = True
