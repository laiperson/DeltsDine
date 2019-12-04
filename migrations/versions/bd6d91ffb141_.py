"""empty message

Revision ID: bd6d91ffb141
Revises: 
Create Date: 2019-12-04 11:16:33.976259

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'bd6d91ffb141'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Meal',
    sa.Column('MealId', sa.INTEGER(), server_default=sa.text('nextval(\'"Meal_MealId_seq"\'::regclass)'), autoincrement=True, nullable=False),
    sa.Column('Date', sa.DATE(), autoincrement=False, nullable=True),
    sa.Column('Description', sa.VARCHAR(length=150), autoincrement=False, nullable=True),
    sa.Column('DinnerBool', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('MealId', name='Meal_pkey')
    )
    op.create_table('Member',
    sa.Column('Email', sa.VARCHAR(length=16), autoincrement=False, nullable=False),
    sa.Column('FirstName', sa.VARCHAR(length=35), autoincrement=False, nullable=False),
    sa.Column('LastName', sa.VARCHAR(length=35), autoincrement=False, nullable=False),
    sa.Column('MealAllowance', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('WeekMealsUsed', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('Active', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('Email', name='Member_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_table('CheckIn',
    sa.Column('MealId', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('UserEmail', sa.VARCHAR(length=16), autoincrement=False, nullable=False),
    sa.Column('Timestamp', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['MealId'], ['Meal.MealId'], name='CheckIn_MealId_fkey'),
    sa.ForeignKeyConstraint(['UserEmail'], ['Member.Email'], name='CheckIn_UserEmail_fkey'),
    sa.PrimaryKeyConstraint('MealId', 'UserEmail', name='CheckIn_pkey')
    )
    op.create_table('RSVP',
    sa.Column('MealId', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('Email', sa.VARCHAR(length=16), autoincrement=False, nullable=False),
    sa.Column('Timestamp', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['Email'], ['Member.Email'], name='Email'),
    sa.ForeignKeyConstraint(['MealId'], ['Meal.MealId'], name='MealId'),
    sa.PrimaryKeyConstraint('MealId', 'Email', name='RSVP_pkey')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Meal')
    op.drop_table('CheckIn')
    op.drop_table('Member')
    op.drop_table('RSVP')
    # ### end Alembic commands ###
