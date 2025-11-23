"""Add rol column to User"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_rol_column_to_user'
down_revision = None  # deja None si es la primera migración que aplica cambios reales
branch_labels = None
depends_on = None


def upgrade():
    # Agregar columna 'rol' con valor por defecto para no romper filas existentes
    op.add_column(
        'users',
        sa.Column('rol', sa.String(), nullable=False, server_default='user')
    )
    # Quitar el default si quieres que en el futuro sea obligatorio en inserts
    op.alter_column('users', 'rol', server_default=None)


def downgrade():
    op.drop_column('users', 'rol')
