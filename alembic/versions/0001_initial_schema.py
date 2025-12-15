"""initial_schema

Revision ID: 0001
Revises: 76cb7f09ee91
Create Date: 2025-12-14 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = '76cb7f09ee91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables in the initial schema."""
    # Note: users table is created in base migration 76cb7f09ee91
    
    # Drop existing tables if they exist (for idempotency)
    # This handles cases where tables were created by previous migrations
    op.execute('DROP TABLE IF EXISTS task_tags CASCADE')
    op.execute('DROP TABLE IF EXISTS tags CASCADE')
    op.execute('DROP TABLE IF EXISTS tag_groups CASCADE')
    op.execute('DROP TABLE IF EXISTS tasks CASCADE')
    op.execute('DROP TABLE IF EXISTS records CASCADE')
    
    # Drop existing indexes if they exist
    op.execute('DROP INDEX IF EXISTS ix_records_occurred_at')
    op.execute('DROP INDEX IF EXISTS ix_records_task_id')
    op.execute('DROP INDEX IF EXISTS ix_records_user_id')
    
    # Create event_type enum for records table
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE event_type AS ENUM ('INPROGRESS', 'PAUSE_START', 'PAUSE_END', 'QUIT', 'COMPLETE');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create records table
    op.create_table(
        'records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mode', sa.Text(), nullable=True),
        sa.Column('place', sa.Text(), nullable=True),
        sa.Column('tool', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('event_type', postgresql.ENUM('INPROGRESS', 'PAUSE_START', 'PAUSE_END', 'QUIT', 'COMPLETE', name='event_type', create_type=False), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='records_user_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='records_pkey')
    )
    op.create_index('ix_records_user_id', 'records', ['user_id'], unique=False)
    op.create_index('ix_records_task_id', 'records', ['task_id'], unique=False)
    op.create_index('ix_records_occurred_at', 'records', ['occurred_at'], unique=False)

    # Create task_status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE taskstatus AS ENUM ('pending', 'in_progress', 'completed', 'archived');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create task_priority enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE taskpriority AS ENUM ('low', 'medium', 'high');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_subtask', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('status', postgresql.ENUM('pending', 'in_progress', 'completed', 'archived', name='taskstatus', create_type=False), nullable=False, server_default='pending'),
        sa.Column('priority', postgresql.ENUM('low', 'medium', 'high', name='taskpriority', create_type=False), nullable=True),
        sa.Column('estimated_minutes', sa.Integer(), nullable=True),
        sa.Column('actual_minutes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='tasks_user_id_fkey'),
        sa.ForeignKeyConstraint(['parent_id'], ['tasks.id'], name='tasks_parent_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='tasks_pkey')
    )

    # Create tag_groups table
    op.create_table(
        'tag_groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False, server_default='custom'),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='tag_groups_user_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='tag_groups_pkey')
    )

    # Create tags table
    op.create_table(
        'tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tag_group_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['tag_group_id'], ['tag_groups.id'], name='tags_tag_group_id_fkey'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='tags_user_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='tags_pkey')
    )

    # Create task_tags join table
    op.create_table(
        'task_tags',
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tag_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], name='task_tags_task_id_fkey', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], name='task_tags_tag_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('task_id', 'tag_id', name='task_tags_pkey')
    )


def downgrade() -> None:
    """Drop all tables and enums."""
    # Drop tables in reverse dependency order using CASCADE
    # CASCADE automatically handles foreign key constraints and dependent objects
    # Note: users table is handled by base migration 76cb7f09ee91
    op.execute('DROP TABLE IF EXISTS task_tags CASCADE')
    op.execute('DROP TABLE IF EXISTS tags CASCADE')
    op.execute('DROP TABLE IF EXISTS tag_groups CASCADE')
    op.execute('DROP TABLE IF EXISTS tasks CASCADE')
    op.execute('DROP TABLE IF EXISTS records CASCADE')

    # Drop enums (CASCADE ensures they're dropped even if still referenced)
    op.execute('DROP TYPE IF EXISTS taskpriority CASCADE')
    op.execute('DROP TYPE IF EXISTS taskstatus CASCADE')
    op.execute('DROP TYPE IF EXISTS event_type CASCADE')
