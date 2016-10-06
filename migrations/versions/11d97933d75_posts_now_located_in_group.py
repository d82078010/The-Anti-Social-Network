"""posts now located in group

Revision ID: 11d97933d75
Revises: 5840bbf84ca
Create Date: 2016-10-06 01:49:57.681013

"""

# revision identifiers, used by Alembic.
revision = '11d97933d75'
down_revision = '5840bbf84ca'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('posts', sa.Column('group_id', sa.Integer))
    op.create_foreign_key('fk_posts_to_group', 'posts', 'group', ['group_id'], ['id'])


def downgrade():
    pass
