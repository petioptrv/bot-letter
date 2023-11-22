import logging
from datetime import datetime
from typing import List

from mjml import mjml_to_html

from app.base_types import NewsletterItem, NewsArticle
from app.core.api_provider import APIProvider
from app.core.config import settings


class NewsletterFormatter:
    @property
    def newsletter_logo_path(self) -> str:
        server_host = settings.IMG_HOST
        link = f"{server_host}/img/icons/newsletter_logo.png"
        return link

    @staticmethod
    def logger() -> logging.Logger:
        return logging.getLogger(__name__)

    def format_newsletter_html_no_new_articles(
        self, newsletter_description: str
    ) -> str:
        nd = newsletter_description
        mjml = f"""
            <mjml>
              <mj-body background-color="#fff">
              <mj-section>
                  <mj-column>
                    <mj-image src={self.newsletter_logo_path} width="300px" height="200px" alt="bot-letter logo" />
                  </mj-column>
              </mj-section>
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

    async def format_newsletter_html(
        self,
        api_provider: APIProvider,
        newsletter_items: List[NewsletterItem],
        newsletter_description: str,
    ) -> str:
        newsletter_items = sorted(
            newsletter_items, key=lambda el: el.relevant, reverse=True
        )
        base_mjml = f"""
            <mjml>
              <mj-body background-color="#fff">
              <mj-section>
                  <mj-column>
                    <mj-image src="{self.newsletter_logo_path}" width="300px" height="200px" alt="Bot-Newsletter Logo"></mj-image>
                  </mj-column>
              </mj-section>
        """
        if not newsletter_items[0].relevant:
            base_mjml += f"""
                <mj-section>
                  <mj-column>
                    <mj-text font-size="16px" color="#555">
                        No new relevant articles found in the past 24 hours for the newsletter description "{newsletter_description}".
                    </mj-text>
                  </mj-column>
                </mj-section>
                """
        else:
            base_mjml += f"""
                <mj-section>
                  <mj-column>
                    <mj-text font-size="16px" color="#555">
                        Here are the most relevant articles found in the past 24 hours for the newsletter description "{newsletter_description}".
                    </mj-text>
                  </mj-column>
                </mj-section>
                """
        irrelevant_message_added = False
        first_article_in_section = True
        divider = '<mj-divider border-color="#555" border-width="1px"></mj-divider>'
        for i, item in enumerate(newsletter_items):
            if not irrelevant_message_added and not item.relevant:
                base_mjml += f"""
                    <mj-section>
                      <mj-column>
                      <mj-divider border-color=\"#555\" border-width=\"3px\"></mj-divider>
                        <mj-text font-size="16px" color="#555">
                            Here are other articles that were most closely related to the newsletter description "{newsletter_description}".
                        </mj-text>
                      </mj-column>
                    </mj-section>
                    """
                irrelevant_message_added = True
                first_article_in_section = True
            publishing_utc_datetime = datetime.utcfromtimestamp(
                item.article.publishing_timestamp
            )
            section = f"""
                <mj-section>
                  <mj-column>
                    {divider if not first_article_in_section else ''}
                    <mj-text font-size="16px" color="#000">
                        <h2><a href={item.article.url}>{item.article.title}</a></h2>
                    </mj-text>
                    <mj-text font-size="14px" color="#999">
                        Published {publishing_utc_datetime.strftime(settings.ARTICLE_PUBLISHED_DT_FORMAT)} UTC.<br>
                    </mj-text>
            """
            first_article_in_section = False
            if item.article.image_url is not None and await self._is_high_res(
                api_provider=api_provider, image_url=item.article.image_url
            ):
                section += f"""<mj-image src="{item.article.image_url}"></mj-image>"""
            elif item.article.image_url is not None:
                self.logger().info(
                    f"Image for article {item.article} is not high res, so is discarded."
                )
            section += """
                    <mj-text font-size=\"16px\" color=\"#ff\">
                    """
            for paragraph in item.summary.summary.split("\n"):
                section += f"""
                        <p>{paragraph}</p>
                """
            section += """
                    </mj-text>
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

    async def _is_high_res(
        self, api_provider: APIProvider, image_url, min_width=600, min_height=300
    ):
        try:
            image = await api_provider.get(url=image_url)
            return image.size[0] >= min_width and image.size[1] >= min_height
        except Exception as e:
            self.logger().exception(f"Error occurred while fetching image: {e}")
        return False


if __name__ == "__main__":
    formatter = NewsletterFormatter()
    txt = f"""{formatter.newsletter_logo_path}"""
    print(txt)
    print(f"exists: {formatter.newsletter_logo_path.exists()}")
