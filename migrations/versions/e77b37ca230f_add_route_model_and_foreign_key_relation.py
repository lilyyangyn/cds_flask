"""add route model and foreign key relation

Revision ID: e77b37ca230f
Revises: d994ed01cbdd
Create Date: 2020-02-14 17:45:03.067471

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e77b37ca230f'
down_revision = 'd994ed01cbdd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('routes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('maxload', sa.Integer(), nullable=True),
    sa.Column('today_load', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.add_column(u'restaurants', sa.Column('route_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'restaurants', 'routes', ['route_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'restaurants', type_='foreignkey')
    op.drop_column(u'restaurants', 'route_id')
    op.drop_table('routes')
    # ### end Alembic commands ###
