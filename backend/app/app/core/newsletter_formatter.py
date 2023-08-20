from typing import List

from mjml import mjml_to_html

from app.base_types import NewsletterItem, Newsletter, NewsArticle


class NewsletterFormatter:
    def format_newsletter(self, newsletter_items: List[NewsletterItem]) -> Newsletter:
        if len(newsletter_items) == 0:
            news_letter_content = (
                f"No news found for {newsletter_items[0].article.search_term}."
            )
        else:
            first_item = newsletter_items[0]
            news_letter_content = self._format_article(article=first_item.article)
            for item in newsletter_items[1:]:
                news_letter_content += (
                    f"---\n\n{self._format_article(article=item.article)}"
                )
        return Newsletter(content=news_letter_content)

    @staticmethod
    def format_newsletter_html_no_new_articles(search_term: str) -> str:
        mjml = f"""
            <mjml>
              <mj-body background-color="#fff">
              <mj-section>
                  <mj-column>
                    <mj-text font-size="16px" color="#555">
                        No new articles found in the past 24 hours for the search term {search_term}.
                    </mj-text>
                  </mj-column>
                </mj-section>
              </mj-section>
              </mj-body>
            </mjml>
        """
        html_output = mjml_to_html(mjml)
        
        return html_output.html

    @staticmethod
    def format_newsletter_html(newsletter_items: List[NewsletterItem]) -> str:
        base_mjml = f"""
            <mjml>
              <mj-body background-color="#fff">
              <mj-section>
                <mj-column>
                    <mj-text font-size="16px" color="#555">Search Term: {newsletter_items[0].article.search_term}</mj-text>
                </mj-column>
              </mj-section>
            """

        for item in newsletter_items:
            section = f"""
                <mj-section>
                  <mj-column>
                    <mj-divider border-color="#555"></mj-divider>
                    <mj-text font-size="16px" color="#000">
                        <h1>{item.article.title}</h1>
                    </mj-text>"""
            for paragraph in item.summary.summary.split("\n"):
                section += f"""
                    <mj-text font-size="16px" color="#555">
                        <p>{paragraph}</p>
                    </mj-text>"""
            section += f"""
                    <mj-text font-size="16px" color="#999">
                        <p><a href={item.article.url}>Read the full article here.</a></p>
                    </mj-text>
                  </mj-column>
                </mj-section>
                """
            base_mjml += section

        base_mjml += """
              </mj-body>
            </mjml>
            """

        html_output = mjml_to_html(base_mjml)

        return html_output.html

    @staticmethod
    def _format_article(article: NewsArticle) -> str:
        return f"{article.title}\n\n{article.content}\n\n{article.url}\n\n"
