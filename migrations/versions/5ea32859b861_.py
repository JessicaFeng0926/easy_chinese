"""empty message

Revision ID: 5ea32859b861
Revises: 7a3559ea3ade
Create Date: 2019-10-05 17:56:22.287933

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5ea32859b861'
down_revision = '7a3559ea3ade'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('lessons', sa.Column('is_delete', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('lessons', 'is_delete')
    # ### end Alembic commands ###
