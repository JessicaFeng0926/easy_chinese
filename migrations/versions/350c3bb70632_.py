"""empty message

Revision ID: 350c3bb70632
Revises: 4e9169cf0aa1
Create Date: 2019-09-23 14:35:50.318549

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '350c3bb70632'
down_revision = '4e9169cf0aa1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('lesson_records',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('talk', sa.String(length=256), nullable=True),
    sa.Column('this_lesson', sa.String(length=256), nullable=True),
    sa.Column('next_lesson', sa.String(length=256), nullable=True),
    sa.Column('homework', sa.String(length=256), nullable=True),
    sa.Column('textbook', sa.String(length=256), nullable=True),
    sa.Column('other', sa.String(length=256), nullable=True),
    sa.Column('lesson_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('lesson_records')
    # ### end Alembic commands ###
