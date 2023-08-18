from app.base_types import Config


class NewsletterCreatorConfig(Config):
    prompt: str = (
        "You are an editor for a newsletter that summarizes articles in up to {word_count} words."
        " The articles are derived using the search term {search_term}. The user will provide you with an article"
        " and you will reply with the summary and only the summary. Feel free to break the summary into easily"
        " digestible paragraphs."
    )
    word_count: int = 200


newsletter_creator_config = NewsletterCreatorConfig()
