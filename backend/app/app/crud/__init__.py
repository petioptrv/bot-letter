from .crud_issue_article import issue_article
from .crud_issue_metrics import issue_metrics
from .crud_newsletter_generation_config import newsletter_generation_config
from .crud_newsletter_issue import newsletter_issue
from .crud_redundancy_prompt import redundancy_prompt
from .crud_relevancy_prompt import relevancy_prompt
from .crud_subscription import subscription
from .crud_token_cost import token_cost
from .crud_user import user

# For a new basic set of CRUD operations you could just do

# from .base import CRUDBase
# from app.models.item import Item
# from app.schemas.item import ItemCreate, ItemUpdate

# item = CRUDBase[Item, ItemCreate, ItemUpdate](Item)
