"""Initial migration

Revision ID: 9516d6feb4bd
Revises: 
Create Date: 2024-07-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9516d6feb4bd'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'item',
        sa.Column('article_number', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('size_in_inches', sa.String(length=100), nullable=True),
        sa.Column('weight', sa.String(length=100), nullable=True),
        sa.Column('photo', sa.Text(), nullable=True),
        sa.Column('thumbnail', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('article_number')
    )


def downgrade():
    op.drop_table('item')
