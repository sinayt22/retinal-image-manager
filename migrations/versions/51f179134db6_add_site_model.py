"""add site model

Revision ID: 51f179134db6
Revises: e6b7f9a07b22
Create Date: 2025-03-16 13:43:28.222565

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '51f179134db6'
down_revision = 'e6b7f9a07b22'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('sites',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('location', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('modified_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    with op.batch_alter_table('images', schema=None) as batch_op:
        batch_op.add_column(sa.Column('site_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_images_site_id', 'sites', ['site_id'], ['id'])
        batch_op.drop_column('site')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('images', schema=None) as batch_op:
        batch_op.add_column(sa.Column('site', sa.VARCHAR(length=255), nullable=True))
        batch_op.drop_constraint('fk_images_site_id', type_='foreignkey')
        batch_op.drop_column('site_id')

    op.drop_table('sites')
    # ### end Alembic commands ###
