"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users table
    op.create_table('users',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('mfa_enabled', sa.Boolean(), nullable=True),
    sa.Column('mfa_secret', sa.String(length=255), nullable=True),
    sa.Column('role', sa.String(length=50), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_verified', sa.Boolean(), nullable=True),
    sa.Column('avatar_url', sa.String(length=500), nullable=True),
    sa.Column('bio', sa.String(length=500), nullable=True),
    sa.Column('plan', sa.String(length=50), nullable=True),
    sa.Column('storage_used_bytes', sa.BigInteger(), nullable=True),
    sa.Column('storage_quota_bytes', sa.BigInteger(), nullable=True),
    sa.Column('last_login', sa.DateTime(), nullable=True),
    sa.Column('email_verified_at', sa.DateTime(), nullable=True),
    sa.Column('phone_verified_at', sa.DateTime(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_phone'), 'users', ['phone'], unique=True)

    # Folders table
    op.create_table('folders',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('owner_user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('parent_folder_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('icon', sa.String(length=50), nullable=True),
    sa.Column('color', sa.String(length=20), nullable=True),
    sa.Column('visibility', sa.String(length=20), nullable=True),
    sa.Column('default_retention_days', sa.Integer(), nullable=True),
    sa.Column('auto_categorize', sa.Boolean(), nullable=True),
    sa.Column('position', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['owner_user_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['parent_folder_id'], ['folders.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )

    # Files table
    op.create_table('files',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('owner_user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('folder_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('filename', sa.String(length=500), nullable=False),
    sa.Column('original_filename', sa.String(length=500), nullable=False),
    sa.Column('size_bytes', sa.BigInteger(), nullable=False),
    sa.Column('mime_type', sa.String(length=100), nullable=False),
    sa.Column('storage_key', sa.Text(), nullable=False),
    sa.Column('storage_bucket', sa.String(length=255), nullable=False),
    sa.Column('checksum_sha256', sa.String(length=64), nullable=False),
    sa.Column('version', sa.Integer(), nullable=True),
    sa.Column('parent_file_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('virus_scan_status', sa.String(length=50), nullable=True),
    sa.Column('virus_scan_at', sa.DateTime(), nullable=True),
    sa.Column('encrypted', sa.Boolean(), nullable=True),
    sa.Column('encryption_key_id', sa.String(length=255), nullable=True),
    sa.Column('ocr_text', sa.Text(), nullable=True),
    sa.Column('ocr_completed', sa.Boolean(), nullable=True),
    sa.Column('extracted_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('thumbnail_url', sa.Text(), nullable=True),
    sa.Column('preview_urls', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('custom_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('accessed_at', sa.DateTime(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['folder_id'], ['folders.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['owner_user_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['parent_file_id'], ['files.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_files_checksum'), 'files', ['checksum_sha256'])

    # Shares table
    op.create_table('shares',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('file_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('sender_user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('sender_name', sa.String(length=255), nullable=True),
    sa.Column('sender_email', sa.String(length=255), nullable=True),
    sa.Column('recipient_user_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('recipient_email', sa.String(length=255), nullable=True),
    sa.Column('recipient_phone', sa.String(length=20), nullable=True),
    sa.Column('recipient_name', sa.String(length=255), nullable=True),
    sa.Column('target_folder_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('target_folder_name', sa.String(length=255), nullable=True),
    sa.Column('message', sa.Text(), nullable=True),
    sa.Column('share_type', sa.String(length=50), nullable=True),
    sa.Column('transaction_id', sa.String(length=100), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('share_token', sa.String(length=255), nullable=True),
    sa.Column('password_hash', sa.String(length=255), nullable=True),
    sa.Column('expires_at', sa.DateTime(), nullable=True),
    sa.Column('max_views', sa.Integer(), nullable=True),
    sa.Column('view_count', sa.Integer(), nullable=True),
    sa.Column('permissions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('delivered_at', sa.DateTime(), nullable=True),
    sa.Column('first_viewed_at', sa.DateTime(), nullable=True),
    sa.Column('last_viewed_at', sa.DateTime(), nullable=True),
    sa.Column('revoked_at', sa.DateTime(), nullable=True),
    sa.Column('share_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('ip_address', sa.String(length=50), nullable=True),
    sa.Column('user_agent', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['file_id'], ['files.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['recipient_user_id'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['sender_user_id'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['target_folder_id'], ['folders.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shares_transaction_id'), 'shares', ['transaction_id'], unique=True)


def downgrade() -> None:
    op.drop_table('shares')
    op.drop_table('files')
    op.drop_table('folders')
    op.drop_table('users')
