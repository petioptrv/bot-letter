from sqlalchemy import Column, Integer, String

from app.db.base_class import Base


class NewsletterGenerationConfig(Base):
    id = Column(Integer, primary_key=True, index=True)
    summary_prompt = Column(String, default="")
    summary_max_word_count = Column(Integer, default=0)
    min_article_description_to_consider_for_article_evaluation_prompts_instead_of_article_summary = Column(
        Integer, default=0
    )
    article_redundancy_prompt = Column(String, default="")
    article_relevancy_prompt = Column(String, default="")
    newsletter_subject_prompt = Column(String, default="")
    max_articles_per_newsletter = Column(Integer, default=0)
    max_processed_articles_per_newsletter = Column(Integer, default=0)
