"""empty message

Revision ID: a47c89866c59
Revises: 
Create Date: 2021-11-21 15:41:19.515949

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a47c89866c59'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_book_info_publish_date'), 'book_info', ['publish_date'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_book_info_publish_date'), table_name='book_info')
    # ### end Alembic commands ###
