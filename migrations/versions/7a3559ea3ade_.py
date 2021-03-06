"""empty message

Revision ID: 7a3559ea3ade
Revises: 350c3bb70632
Create Date: 2019-09-27 16:06:08.889741

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a3559ea3ade'
down_revision = '350c3bb70632'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('lessons', sa.Column('mark', sa.Integer(), nullable=True))
    op.add_column('lessons', sa.Column('s_comment', sa.String(length=256), nullable=True))
    op.add_column('lessons', sa.Column('t_comment', sa.String(length=256), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('lessons', 't_comment')
    op.drop_column('lessons', 's_comment')
    op.drop_column('lessons', 'mark')
    # ### end Alembic commands ###
