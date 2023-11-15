from app.base_types import Config


class NewsletterCreatorConfig(Config):
    summary_prompt: str = (
        "You are an editor for a newsletter that summarizes articles in up to {word_count} words."
        " The user will provide you with an article and you will reply with the summary and only"
        " the summary. Feel free to break the summary into easily digestible paragraphs."
    )
    word_count: int = 200
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
    newsletter_subject_prompt: str = (
        "You are a newsletter editor curating articles for a newsletter. Your task is to come up with an email"
        " subject for the latest newsletter email. I will provide you with the content of the newsletter and you"
        " have to reply with the newsletter subject line. I only want the subject line and nothing else."
        " Here is the content of the newsletter:\n\n{newsletter_content}"
    )
    max_articles_per_newsletter: int = 5
    max_irrelevant_articles_count: int = 5


newsletter_creator_config = NewsletterCreatorConfig()
