"""settings: multi-channel prefs and mute flags

Revision ID: c50ef7cb8e46
Revises: cf8d678f8a2c
Create Date: 2026-07-01 11:09:36.523011

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c50ef7cb8e46'
down_revision: Union[str, None] = 'cf8d678f8a2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('subscriber_channel_valid', 'subscribers', type_='check')
    op.drop_constraint('subscriber_exactly_one_contact', 'subscribers', type_='check')

    op.add_column(
        'subscribers', sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default=sa.true())
    )
    op.add_column(
        'subscribers', sa.Column('sms_enabled', sa.Boolean(), nullable=False, server_default=sa.false())
    )
    op.add_column(
        'subscribers', sa.Column('mute_movers', sa.Boolean(), nullable=False, server_default=sa.false())
    )
    op.add_column(
        'subscribers', sa.Column('mute_restocks', sa.Boolean(), nullable=False, server_default=sa.false())
    )
    op.add_column(
        'subscribers', sa.Column('mute_news', sa.Boolean(), nullable=False, server_default=sa.false())
    )
    op.add_column('subscribers', sa.Column('pending_contact', sa.String(length=255), nullable=True))

    # Backfill email_enabled/sms_enabled from the old single channel column
    # before dropping it, so any pre-existing rows keep their delivery channel.
    op.execute("UPDATE subscribers SET email_enabled = (channel = 'email'), sms_enabled = (channel = 'sms')")

    op.drop_column('subscribers', 'channel')

    op.create_check_constraint('subscriber_has_a_contact', 'subscribers', 'email IS NOT NULL OR phone IS NOT NULL')
    op.create_check_constraint(
        'subscriber_email_enabled_needs_email', 'subscribers', 'NOT email_enabled OR email IS NOT NULL'
    )
    op.create_check_constraint(
        'subscriber_sms_enabled_needs_phone', 'subscribers', 'NOT sms_enabled OR phone IS NOT NULL'
    )
    op.create_check_constraint(
        'subscriber_at_least_one_channel_enabled', 'subscribers', 'email_enabled OR sms_enabled'
    )


def downgrade() -> None:
    op.drop_constraint('subscriber_at_least_one_channel_enabled', 'subscribers', type_='check')
    op.drop_constraint('subscriber_sms_enabled_needs_phone', 'subscribers', type_='check')
    op.drop_constraint('subscriber_email_enabled_needs_email', 'subscribers', type_='check')
    op.drop_constraint('subscriber_has_a_contact', 'subscribers', type_='check')

    op.add_column('subscribers', sa.Column('channel', sa.VARCHAR(length=16), autoincrement=False, nullable=True))
    op.execute("UPDATE subscribers SET channel = CASE WHEN email_enabled THEN 'email' ELSE 'sms' END")
    op.alter_column('subscribers', 'channel', nullable=False)

    op.drop_column('subscribers', 'pending_contact')
    op.drop_column('subscribers', 'mute_news')
    op.drop_column('subscribers', 'mute_restocks')
    op.drop_column('subscribers', 'mute_movers')
    op.drop_column('subscribers', 'sms_enabled')
    op.drop_column('subscribers', 'email_enabled')

    op.create_check_constraint('subscriber_channel_valid', 'subscribers', "channel IN ('email', 'sms')")
    op.create_check_constraint(
        'subscriber_exactly_one_contact', 'subscribers', '(email IS NOT NULL) != (phone IS NOT NULL)'
    )
    # ### end Alembic commands ###
