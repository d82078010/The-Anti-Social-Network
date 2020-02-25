"""now we have groups

Revision ID: 5840bbf84ca
Revises: 24bbd91236b
Create Date: 2016-10-06 00:52:38.263425

"""

# revision identifiers, used by Alembic.
revision = '5840bbf84ca'
down_revision = '24bbd91236b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('groups',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('description', sa.Text(), nullable=False),
                    sa.Column('public', sa.Boolean(), nullable=False),
                    sa.Column('admin_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id'))


def downgrade():
    pass
