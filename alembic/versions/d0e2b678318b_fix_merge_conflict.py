"""fix merge conflict

Revision ID: d0e2b678318b
Revises: d4b6d1b1b65e, f5b467180622
Create Date: 2025-12-14 11:33:49.576894

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0e2b678318b'
down_revision: Union[str, Sequence[str], None] = ('d4b6d1b1b65e', 'f5b467180622')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
