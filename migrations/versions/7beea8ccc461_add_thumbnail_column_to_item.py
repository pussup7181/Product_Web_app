"""Add thumbnail column to Item

Revision ID: 7beea8ccc461
Revises: 9516d6feb4bd
Create Date: 2024-07-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7beea8ccc461'
down_revision = '9516d6feb4bd'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('item', sa.Column('thumbnail', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('item', 'thumbnail')
