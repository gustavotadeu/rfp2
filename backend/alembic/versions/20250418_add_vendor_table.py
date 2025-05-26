"""
Alembic migration: Add Vendor table
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'vendors',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('nome', sa.String(255), nullable=False),
        sa.Column('tecnologias', sa.Text, nullable=True),
        sa.Column('produtos', sa.Text, nullable=True),
        sa.Column('certificacoes', sa.Text, nullable=True),
        sa.Column('requisitos_atendidos', sa.Text, nullable=True),
    )

def downgrade():
    op.drop_table('vendors')
