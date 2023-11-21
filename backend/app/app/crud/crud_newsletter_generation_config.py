from typing import Optional, TYPE_CHECKING

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import NewsletterGenerationConfig
from app.schemas.newsletter_generation_config import (
    NewsletterGenerationConfigCreate,
    NewsletterGenerationConfigUpdate,
)

if TYPE_CHECKING:
    from app.core.newsletter_creator.newsletter_creator_utils import NewsletterCreatorConfig


class CRUDNewsletterGenerationConfig(
    CRUDBase[
        NewsletterGenerationConfig,
        NewsletterGenerationConfigCreate,
        NewsletterGenerationConfigUpdate,
    ]
):
    def create(
        self, db: Session, *, obj_in: NewsletterGenerationConfigCreate
    ) -> NewsletterGenerationConfig:
        obj_in_data = jsonable_encoder(obj_in)
        obj_in_data.pop("version", None)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_config(
        self, db: Session, *, config_in: "NewsletterCreatorConfig"
    ) -> Optional[NewsletterGenerationConfig]:
        return (
            db.query(self.model)
            .filter(
                NewsletterGenerationConfig.summary_prompt == config_in.summary_prompt,
                NewsletterGenerationConfig.summary_max_word_count
                == config_in.summary_max_word_count,
                NewsletterGenerationConfig.min_article_description_to_consider_for_article_evaluation_prompts_instead_of_article_summary
                == config_in.min_article_description_to_consider_for_article_evaluation_prompts_instead_of_article_summary,
                NewsletterGenerationConfig.article_redundancy_prompt
                == config_in.article_redundancy_prompt,
                NewsletterGenerationConfig.article_relevancy_prompt
                == config_in.article_relevancy_prompt,
                NewsletterGenerationConfig.newsletter_subject_prompt
                == config_in.newsletter_subject_prompt,
                NewsletterGenerationConfig.max_articles_per_newsletter
                == config_in.max_articles_per_newsletter,
                NewsletterGenerationConfig.max_processed_articles_per_newsletter
                == config_in.max_processed_articles_per_newsletter,
            )
            .first()
        )


newsletter_generation_config = CRUDNewsletterGenerationConfig(
    NewsletterGenerationConfig
)
