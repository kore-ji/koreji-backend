"""add unique constraint to records table

Revision ID: 096717a1c7e7
Revises: 0001
Create Date: 2025-12-14 09:07:19.878912

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '096717a1c7e7'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add unique constraint on records.id (though primary key already enforces uniqueness)
    op.create_unique_constraint('records_id_unique', 'records', ['id'])
    op.create_unique_constraint('users_id_unique', 'users', ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the unique constraint
    op.drop_constraint('records_id_unique', 'records', type_='unique')
    op.drop_constraint('users_id_unique', 'users', type_='unique')