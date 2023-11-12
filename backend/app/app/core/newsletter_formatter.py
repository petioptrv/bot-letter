import logging
from typing import List

from mjml import mjml_to_html

from app.base_types import NewsletterItem, NewsArticle
from app.core.api_provider import APIProvider


class NewsletterFormatter:
    @staticmethod
    def logger() -> logging.Logger:
        return logging.getLogger(__name__)

    @staticmethod
    def format_newsletter_html_no_new_articles(newsletter_description: str) -> str:
        nd = newsletter_description
        mjml = f"""
            <mjml>
              <mj-body background-color="#fff">
              <mj-section>
                  <mj-column>
                    <mj-text font-size="16px" color="#555">
                        No new articles found in the past 24 hours for the newsletter description "{nd}".
                    </mj-text>
                  </mj-column>
                </mj-section>
              </mj-section>
              </mj-body>
            </mjml>
        """
        html_output = mjml_to_html(mjml)

        return html_output.html

    async def format_newsletter_html(self, api_provider: APIProvider, newsletter_items: List[NewsletterItem]) -> str:
        base_mjml = """
            <mjml>
              <mj-body background-color="#fff">
        """
        for i, item in enumerate(newsletter_items):
            section = f"""
                <mj-section>
                  <mj-column>
                    {'<mj-divider border-color="#555" border-width="1px"></mj-divider>' if i != 0 else ''}
                    <mj-text font-size="16px" color="#000">
                        <h2>{item.article.title}</h2>
                    </mj-text>
            """
            if item.article.image_url is not None and await self._is_high_res(
                api_provider=api_provider, image_url=item.article.image_url
            ):
                section += f"""<mj-image src="{item.article.image_url}"></mj-image>"""
            else:
                self.logger().info(f"Image for article {item.article} is not high res, so is discarded.")
            for paragraph in item.summary.summary.split("\n"):
                section += f"""
                    <mj-text font-size="16px" color="#ff">
                        <p>{paragraph}</p>
                    </mj-text>
                """
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

    async def _is_high_res(self, api_provider: APIProvider, image_url, min_width=600, min_height=300):
        try:
            image = await api_provider.get(url=image_url)
            return image.size[0] >= min_width and image.size[1] >= min_height
        except Exception as e:
            self.logger().exception(f"Error occurred while fetching image: {e}")
        return False
