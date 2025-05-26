"""create_ai_prompts_table

Revision ID: 20250423_ai_prompts
Revises: <REPLACE_WITH_PREVIOUS_REVISION_ID> 
Create Date: 2024-04-23 10:00:00.000000 

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250423_ai_prompts'
down_revision: Union[str, None] = '20250422_add_escopo_servico' # Set to the assumed revision of the previous file
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_prompts',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('prompt_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_prompts_id'), 'ai_prompts', ['id'], unique=False)
    op.create_index(op.f('ix_ai_prompts_name'), 'ai_prompts', ['name'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_ai_prompts_name'), table_name='ai_prompts')
    op.drop_index(op.f('ix_ai_prompts_id'), table_name='ai_prompts')
    op.drop_table('ai_prompts')
