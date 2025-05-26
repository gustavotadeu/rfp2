"""
Alembic migration: Add EscopoServico table
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'escopo_servico',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('rfp_id', sa.Integer, sa.ForeignKey('rfps.id'), nullable=False),
        sa.Column('titulo', sa.String(255), nullable=False),
        sa.Column('descricao', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

def downgrade():
    op.drop_table('escopo_servico')
