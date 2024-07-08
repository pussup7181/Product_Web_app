from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '68dbe52ed831'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add the new columns with default values
    with op.batch_alter_table('item') as batch_op:
        batch_op.add_column(sa.Column('size_in_mm', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('weight_in_g', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('thumbnail', sa.LargeBinary(), nullable=True))

    # Set default values for existing rows
    op.execute('UPDATE item SET size_in_mm = 0 WHERE size_in_mm IS NULL')
    op.execute('UPDATE item SET weight_in_g = 0 WHERE weight_in_g IS NULL')

    # Alter columns to set them as NOT NULL
    with op.batch_alter_table('item') as batch_op:
        batch_op.alter_column('size_in_mm', nullable=False)
        batch_op.alter_column('weight_in_g', nullable=False)


def downgrade():
    with op.batch_alter_table('item') as batch_op:
        batch_op.drop_column('size_in_mm')
        batch_op.drop_column('weight_in_g')
        batch_op.drop_column('thumbnail')
