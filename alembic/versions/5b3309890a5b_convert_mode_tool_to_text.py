"""convert_mode_tool_to_text

Revision ID: 5b3309890a5b
Revises: d0e2b678318b
Create Date: 2025-12-14 03:55:08.653913

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b3309890a5b'
down_revision: Union[str, Sequence[str], None] = 'd0e2b678318b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Convert mode column from enum to text in records table
    op.execute("ALTER TABLE records ALTER COLUMN mode TYPE TEXT USING mode::text")
    
    # Convert mode column from enum to text in user_context table
    op.execute("ALTER TABLE user_context ALTER COLUMN mode TYPE TEXT USING mode::text")
    
    # Convert tool column from array of enum to array of text in records table
    op.execute("ALTER TABLE records ALTER COLUMN tool TYPE TEXT[] USING tool::text[]")
    
    # Convert tool column from array of enum to array of text in user_context table
    op.execute("ALTER TABLE user_context ALTER COLUMN tool TYPE TEXT[] USING tool::text[]")
    
    # Drop the enum types (now safe since no tables use them)
    op.execute("DROP TYPE IF EXISTS modeenum")
    op.execute("DROP TYPE IF EXISTS toolenum")


def downgrade() -> None:
    """Downgrade schema."""
    # Recreate the enum types
    op.execute("CREATE TYPE modeenum AS ENUM ('noSelect', 'relax', 'focus', 'exercise', 'social')")
    op.execute("CREATE TYPE toolenum AS ENUM ('noSelect', 'Phone', 'computer', 'ipad', 'textbook', 'notebook')")
    
    # Convert mode column back to enum in records table
    op.execute("ALTER TABLE records ALTER COLUMN mode TYPE modeenum USING mode::modeenum")
    
    # Convert mode column back to enum in user_context table
    op.execute("ALTER TABLE user_context ALTER COLUMN mode TYPE modeenum USING mode::modeenum")
    
    # Convert tool column back to array of enum in records table
    op.execute("ALTER TABLE records ALTER COLUMN tool TYPE toolenum[] USING tool::toolenum[]")
    
    # Convert tool column back to array of enum in user_context table
    op.execute("ALTER TABLE user_context ALTER COLUMN tool TYPE toolenum[] USING tool::toolenum[]")
