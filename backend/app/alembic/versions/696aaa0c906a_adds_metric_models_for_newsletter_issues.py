"""adds metric models for newsletter issues

Revision ID: 696aaa0c906a
Revises: 34b2e3d4948f
Create Date: 2023-11-22 10:50:20.698271

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '696aaa0c906a'
down_revision = '34b2e3d4948f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('newsletter_generation_config',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('summary_prompt', sa.String(), nullable=True),
    sa.Column('summary_max_word_count', sa.Integer(), nullable=True),
    sa.Column('min_description_len_for_evaluation_prompts', sa.Integer(), nullable=True),
    sa.Column('article_redundancy_prompt', sa.String(), nullable=True),
    sa.Column('article_relevancy_prompt', sa.String(), nullable=True),
    sa.Column('newsletter_subject_prompt', sa.String(), nullable=True),
    sa.Column('max_articles_per_newsletter', sa.Integer(), nullable=True),
    sa.Column('max_processed_articles_per_newsletter', sa.Integer(), nullable=True),
    sa.Column('text_generation_model', sa.String(), nullable=True),
    sa.Column('decision_model', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_newsletter_generation_config_id'), 'newsletter_generation_config', ['id'], unique=False)
    op.create_table('newsletter_issue',
    sa.Column('issue_id', sa.String(length=32), nullable=False),
    sa.Column('subscription_id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['subscription_id'], ['subscription.id'], ),
    sa.PrimaryKeyConstraint('issue_id')
    )
    op.create_index(op.f('ix_newsletter_issue_issue_id'), 'newsletter_issue', ['issue_id'], unique=False)
    op.create_table('issue_article',
    sa.Column('issue_id', sa.String(length=32), nullable=False),
    sa.Column('article_id', sa.String(length=32), nullable=False),
    sa.ForeignKeyConstraint(['issue_id'], ['newsletter_issue.issue_id'], ),
    sa.PrimaryKeyConstraint('issue_id', 'article_id'),
    sa.UniqueConstraint('article_id')
    )
    op.create_table('issue_metrics',
    sa.Column('issue_id', sa.String(length=32), nullable=False),
    sa.Column('newsletter_generation_config_id', sa.Integer(), nullable=False),
    sa.Column('time_to_generate', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['issue_id'], ['newsletter_issue.issue_id'], ),
    sa.ForeignKeyConstraint(['newsletter_generation_config_id'], ['newsletter_generation_config.id'], ),
    sa.PrimaryKeyConstraint('issue_id', 'newsletter_generation_config_id')
    )
    op.create_table('token_cost',
    sa.Column('issue_id', sa.String(length=32), nullable=False),
    sa.Column('article_id', sa.String(length=32), nullable=False),
    sa.Column('action', sa.String(length=32), nullable=False),
    sa.Column('input_tokens', sa.Integer(), nullable=True),
    sa.Column('output_tokens', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['article_id'], ['issue_article.article_id'], ),
    sa.ForeignKeyConstraint(['issue_id'], ['newsletter_issue.issue_id'], ),
    sa.PrimaryKeyConstraint('issue_id', 'article_id', 'action')
    )
    op.drop_index('ix_newslettergenerationconfig_id', table_name='newslettergenerationconfig')
    op.drop_table('newslettergenerationconfig')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('newslettergenerationconfig',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('summary_prompt', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('summary_max_word_count', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('article_redundancy_prompt', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('article_relevancy_prompt', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('newsletter_subject_prompt', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('max_articles_per_newsletter', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('max_processed_articles_per_newsletter', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('min_description_len_for_evaluation_prompts', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('text_generation_model', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('decision_model', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='newslettergenerationconfig_pkey')
    )
    op.create_index('ix_newslettergenerationconfig_id', 'newslettergenerationconfig', ['id'], unique=False)
    op.drop_table('token_cost')
    op.drop_table('issue_metrics')
    op.drop_table('issue_article')
    op.drop_index(op.f('ix_newsletter_issue_issue_id'), table_name='newsletter_issue')
    op.drop_table('newsletter_issue')
    op.drop_index(op.f('ix_newsletter_generation_config_id'), table_name='newsletter_generation_config')
    op.drop_table('newsletter_generation_config')
    # ### end Alembic commands ###
