"""empty message

Revision ID: 4e9169cf0aa1
Revises: a6b74481cdd4
Create Date: 2019-09-16 11:01:41.029746

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4e9169cf0aa1'
down_revision = 'a6b74481cdd4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('student_profiles', sa.Column('age', sa.String(length=32), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('student_profiles', 'age')
    # ### end Alembic commands ###
