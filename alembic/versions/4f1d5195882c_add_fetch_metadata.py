"""Add fetch metadata

Revision ID: 4f1d5195882c
Revises: 7846e4e5fb8e
Create Date: 2023-11-29 06:38:10.062424

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4f1d5195882c'
down_revision: Union[str, None] = '7846e4e5fb8e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    sa.Enum('OK', 'FETCHING', 'GONE', 'NOT_FOUND', 'FAILED', 'TRY_LATER', name='feedstatus').create(op.get_bind())
    op.add_column('feed', sa.Column('status', postgresql.ENUM('OK', 'FETCHING', 'GONE', 'NOT_FOUND', 'FAILED', 'TRY_LATER', name='feedstatus', create_type=False), nullable=True))
    op.add_column('feed', sa.Column('last_fetch', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('feed', 'last_fetch')
    op.drop_column('feed', 'status')
    sa.Enum('OK', 'FETCHING', 'GONE', 'NOT_FOUND', 'FAILED', 'TRY_LATER', name='feedstatus').drop(op.get_bind())
    # ### end Alembic commands ###