"""
Alembic migration: Add fabricante_escolhido_id and analise_vendors to RFP
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('rfps', sa.Column('fabricante_escolhido_id', sa.Integer(), sa.ForeignKey('vendors.id'), nullable=True))
    op.add_column('rfps', sa.Column('analise_vendors', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('rfps', 'fabricante_escolhido_id')
    op.drop_column('rfps', 'analise_vendors')
