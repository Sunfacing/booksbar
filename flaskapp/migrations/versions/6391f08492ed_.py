"""empty message

Revision ID: 6391f08492ed
Revises: 8b5da17bb4ae
Create Date: 2021-11-01 17:45:04.032384

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6391f08492ed'
down_revision = '8b5da17bb4ae'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('book_info', sa.Column('isbn', sa.String(length=30), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('book_info', 'isbn')
    # ### end Alembic commands ###
