"""attempts to simplify relations

Revision ID: f86e7363681e
Revises: ef0bbbbc6782
Create Date: 2023-11-22 14:11:03.441869

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f86e7363681e'
down_revision = 'ef0bbbbc6782'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('issue_metrics', sa.Column('metrics_id', sa.Integer(), nullable=False))
    op.create_index(op.f('ix_issue_metrics_metrics_id'), 'issue_metrics', ['metrics_id'], unique=True)
    op.add_column('token_cost', sa.Column('token_cost_id', sa.Integer(), nullable=False))
    op.add_column('token_cost', sa.Column('metrics_id', sa.Integer(), nullable=False))
    op.create_index(op.f('ix_token_cost_token_cost_id'), 'token_cost', ['token_cost_id'], unique=False)
    op.create_foreign_key(None, 'token_cost', 'issue_metrics', ['metrics_id'], ['metrics_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'token_cost', type_='foreignkey')
    op.drop_index(op.f('ix_token_cost_token_cost_id'), table_name='token_cost')
    op.drop_column('token_cost', 'metrics_id')
    op.drop_column('token_cost', 'token_cost_id')
    op.drop_index(op.f('ix_issue_metrics_metrics_id'), table_name='issue_metrics')
    op.drop_column('issue_metrics', 'metrics_id')
    # ### end Alembic commands ###
