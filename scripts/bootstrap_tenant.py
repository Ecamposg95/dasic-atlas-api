from pathlib import Path
import sys

from sqlalchemy import text


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import models
from app.db import SessionLocal, engine


def bootstrap_tenant() -> None:
    models.Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        ddl_statements = [
            "ALTER TABLE IF EXISTS clientes ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36)",
            "ALTER TABLE IF EXISTS transacciones_clientes ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36)",
            "ALTER TABLE IF EXISTS ordenes_venta ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36)",
            "ALTER TABLE IF EXISTS detalles_orden ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36)",
            "CREATE INDEX IF NOT EXISTS ix_clientes_organization_id ON clientes (organization_id)",
            "CREATE INDEX IF NOT EXISTS ix_transacciones_clientes_organization_id ON transacciones_clientes (organization_id)",
            "CREATE INDEX IF NOT EXISTS ix_ordenes_venta_organization_id ON ordenes_venta (organization_id)",
            "CREATE INDEX IF NOT EXISTS ix_detalles_orden_organization_id ON detalles_orden (organization_id)",
        ]
        for statement in ddl_statements:
            db.execute(text(statement))
        db.commit()

        org = db.query(models.Organization).filter(models.Organization.name == "DASIC Industrial").first()
        if not org:
            org = models.Organization(name="DASIC Industrial", industry_type="DASIC_INDUSTRIAL")
            db.add(org)
            db.commit()
            db.refresh(org)

        hq = (
            db.query(models.Branch)
            .filter(
                models.Branch.organization_id == org.id,
                models.Branch.branch_type == models.BranchType.HQ,
            )
            .first()
        )
        if not hq:
            hq = models.Branch(
                organization_id=org.id,
                name="HQ",
                branch_type=models.BranchType.HQ,
            )
            db.add(hq)
            db.commit()
            db.refresh(hq)

        users = db.query(models.Usuario).all()
        created_memberships = 0
        for user in users:
            exists = (
                db.query(models.UserOrganization)
                .filter(
                    models.UserOrganization.user_id == user.id,
                    models.UserOrganization.organization_id == org.id,
                )
                .first()
            )
            if not exists:
                db.add(
                    models.UserOrganization(
                        user_id=user.id,
                        organization_id=org.id,
                        branch_id=hq.id,
                        is_active=True,
                    )
                )
                created_memberships += 1
        db.commit()

        c1 = db.query(models.Cliente).filter(models.Cliente.organization_id.is_(None)).update(
            {models.Cliente.organization_id: org.id}, synchronize_session=False
        )
        c2 = db.query(models.TransaccionCliente).filter(
            models.TransaccionCliente.organization_id.is_(None)
        ).update({models.TransaccionCliente.organization_id: org.id}, synchronize_session=False)
        c3 = db.query(models.OrdenVenta).filter(models.OrdenVenta.organization_id.is_(None)).update(
            {models.OrdenVenta.organization_id: org.id}, synchronize_session=False
        )
        c4 = db.query(models.DetalleOrden).filter(models.DetalleOrden.organization_id.is_(None)).update(
            {models.DetalleOrden.organization_id: org.id}, synchronize_session=False
        )
        db.commit()

        print("Tenant bootstrap complete")
        print(f"Organization: {org.id} ({org.name})")
        print(f"HQ Branch: {hq.id}")
        print(f"Memberships created: {created_memberships}")
        print(f"Backfilled clientes: {c1}")
        print(f"Backfilled transacciones_clientes: {c2}")
        print(f"Backfilled ordenes_venta: {c3}")
        print(f"Backfilled detalles_orden: {c4}")
    finally:
        db.close()


if __name__ == "__main__":
    bootstrap_tenant()
