"""Make filename nullable for playlist schedules

Revision ID: e3d80371ffd1
Revises: 080ce83ae317
Create Date: 2025-10-29 19:39:08.693279

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e3d80371ffd1'
down_revision = '080ce83ae317'
branch_labels = None
depends_on = None


def upgrade():
    # For SQLite, we need to recreate the table to change column constraints
    # First, create the new table with the correct schema
    op.create_table('schedule_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('schedule_list_id', sa.Integer(), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=True),  # Now nullable
        sa.Column('time', sa.String(length=5), nullable=False),
        sa.Column('monday', sa.Boolean(), nullable=True),
        sa.Column('tuesday', sa.Boolean(), nullable=True),
        sa.Column('wednesday', sa.Boolean(), nullable=True),
        sa.Column('thursday', sa.Boolean(), nullable=True),
        sa.Column('friday', sa.Boolean(), nullable=True),
        sa.Column('saturday', sa.Boolean(), nullable=True),
        sa.Column('sunday', sa.Boolean(), nullable=True),
        sa.Column('is_muted', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('schedule_type', sa.String(length=20), nullable=True),
        sa.Column('folder_path', sa.String(length=500), nullable=True),
        sa.Column('playlist_duration', sa.Integer(), nullable=True),
        sa.Column('track_interval', sa.Integer(), nullable=True),
        sa.Column('max_tracks', sa.Integer(), nullable=True),
        sa.Column('shuffle_mode', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['schedule_list_id'], ['schedule_list.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Copy data from old table to new table
    op.execute("""
        INSERT INTO schedule_new (
            id, schedule_list_id, filename, time, monday, tuesday, wednesday, 
            thursday, friday, saturday, sunday, is_muted, created_at,
            schedule_type, folder_path, playlist_duration, track_interval, 
            max_tracks, shuffle_mode
        )
        SELECT 
            id, schedule_list_id, filename, time, monday, tuesday, wednesday, 
            thursday, friday, saturday, sunday, is_muted, created_at,
            schedule_type, folder_path, playlist_duration, track_interval, 
            max_tracks, shuffle_mode
        FROM schedule
    """)
    
    # Drop old table and rename new table
    op.drop_table('schedule')
    op.rename_table('schedule_new', 'schedule')


def downgrade():
    # Reverse the operation - make filename NOT NULL again
    op.create_table('schedule_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('schedule_list_id', sa.Integer(), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=False),  # Back to NOT NULL
        sa.Column('time', sa.String(length=5), nullable=False),
        sa.Column('monday', sa.Boolean(), nullable=True),
        sa.Column('tuesday', sa.Boolean(), nullable=True),
        sa.Column('wednesday', sa.Boolean(), nullable=True),
        sa.Column('thursday', sa.Boolean(), nullable=True),
        sa.Column('friday', sa.Boolean(), nullable=True),
        sa.Column('saturday', sa.Boolean(), nullable=True),
        sa.Column('sunday', sa.Boolean(), nullable=True),
        sa.Column('is_muted', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('schedule_type', sa.String(length=20), nullable=True),
        sa.Column('folder_path', sa.String(length=500), nullable=True),
        sa.Column('playlist_duration', sa.Integer(), nullable=True),
        sa.Column('track_interval', sa.Integer(), nullable=True),
        sa.Column('max_tracks', sa.Integer(), nullable=True),
        sa.Column('shuffle_mode', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['schedule_list_id'], ['schedule_list.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Copy only records that have filename (playlist schedules will be lost)
    op.execute("""
        INSERT INTO schedule_old (
            id, schedule_list_id, filename, time, monday, tuesday, wednesday, 
            thursday, friday, saturday, sunday, is_muted, created_at,
            schedule_type, folder_path, playlist_duration, track_interval, 
            max_tracks, shuffle_mode
        )
        SELECT 
            id, schedule_list_id, filename, time, monday, tuesday, wednesday, 
            thursday, friday, saturday, sunday, is_muted, created_at,
            schedule_type, folder_path, playlist_duration, track_interval, 
            max_tracks, shuffle_mode
        FROM schedule
        WHERE filename IS NOT NULL
    """)
    
    op.drop_table('schedule')
    op.rename_table('schedule_old', 'schedule')
