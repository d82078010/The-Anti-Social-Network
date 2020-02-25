"""users can join in groups

Revision ID: 5ae87c4d29
Revises: 5840bbf84ca
Create Date: 2016-10-06 14:47:26.979405

"""

# revision identifiers, used by Alembic.
revision = '5ae87c4d29'
down_revision = '5840bbf84ca'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('users_groups',
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.Column('group_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
                    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
                    sa.PrimaryKeyConstraint('user_id', 'group_id'))



def downgrade():
    pass
