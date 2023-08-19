"""removes items

Revision ID: 2da15850c3c9
Revises: 8c49390b7647
Create Date: 2023-08-19 19:16:19.602963

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2da15850c3c9'
down_revision = '8c49390b7647'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_item_description', table_name='item')
    op.drop_index('ix_item_id', table_name='item')
    op.drop_index('ix_item_title', table_name='item')
    op.drop_table('item')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('item',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('title', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='item_pkey')
    )
    op.create_index('ix_item_title', 'item', ['title'], unique=False)
    op.create_index('ix_item_id', 'item', ['id'], unique=False)
    op.create_index('ix_item_description', 'item', ['description'], unique=False)
    # ### end Alembic commands ###
