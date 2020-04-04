"""empty message

Revision ID: b75b1f4ef82d
Revises: adf84c2ead7e
Create Date: 2020-04-04 16:08:19.542651

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b75b1f4ef82d'
down_revision = 'adf84c2ead7e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('teacher_profiles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('education', sa.String(length=256), nullable=True),
    sa.Column('personality', sa.String(length=128), nullable=True),
    sa.Column('hobby', sa.String(length=128), nullable=True),
    sa.Column('courses', sa.String(length=256), nullable=True),
    sa.Column('comments', sa.String(length=256), nullable=True),
    sa.Column('teacher_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('teacher_profiles')
    # ### end Alembic commands ###
