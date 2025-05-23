"""Init

Revision ID: be514a6b3e4d
Revises: 
Create Date: 2025-01-29 21:33:48.285560

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'be514a6b3e4d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('gender', sa.Enum('male', 'female', name='genderenum'), nullable=False),
    sa.Column('is_trainer', sa.Boolean(), nullable=False),
    sa.Column('is_admin', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
    sa.Column('trainer_id', sa.BigInteger(), nullable=True),
    sa.ForeignKeyConstraint(['trainer_id'], ['users.user_id'], ),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_table('appointments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('start_at', sa.DateTime(), nullable=False),
    sa.Column('is_confirmation', sa.Boolean(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('comment', sa.String(), nullable=True),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('trainer_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['trainer_id'], ['users.user_id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('schedule_works',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('hours', sa.ARRAY(sa.Integer()), nullable=True),
    sa.Column('free_days', sa.ARRAY(sa.Integer()), nullable=True),
    sa.Column('max_user_per_hour', sa.Integer(), nullable=False),
    sa.Column('auto_confirmation', sa.Boolean(), nullable=False),
    sa.Column('trainer_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['trainer_id'], ['users.user_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('schedule_works')
    op.drop_table('appointments')
    op.drop_table('users')
    # ### end Alembic commands ###
