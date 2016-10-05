"""add like feature in post

Revision ID: 24bbd91236b
Revises: 47b4ac7d7d6e
Create Date: 2016-10-05 01:38:18.406965

"""

# revision identifiers, used by Alembic.
revision = '24bbd91236b'
down_revision = '47b4ac7d7d6e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('posts', sa.Column('like_count', sa.Integer, server_default='0'))

    op.create_table('posts_likes',
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.Column('post_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
                    sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ),
                    sa.PrimaryKeyConstraint('user_id', 'post_id'))
    pass


def downgrade():
    pass
