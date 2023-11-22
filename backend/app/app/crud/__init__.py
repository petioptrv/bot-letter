from .crud_user import user
from .crud_subscription import subscription
from .crud_newsletter_generation_config import newsletter_generation_config
from .crud_newsletter_issue import newsletter_issue
from .crud_issue_article import issue_article
from .crud_issue_metrics import issue_metrics
from .crud_token_cost import token_cost

# For a new basic set of CRUD operations you could just do

# from .base import CRUDBase
# from app.models.item import Item
# from app.schemas.item import ItemCreate, ItemUpdate

# item = CRUDBase[Item, ItemCreate, ItemUpdate](Item)
