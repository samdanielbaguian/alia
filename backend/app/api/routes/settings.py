"""
Routes for platform settings management.

Provides endpoints for:
- Retrieving current platform settings
- Updating platform settings (admin only)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_db, get_current_admin  # ← Import absolu
from app.models.settings import SettingsModel        # ← Import absolu

router = APIRouter()


# ─── Schéma de mise à jour ───────────────────────────────────────────────────

class SettingsUpdateRequest(BaseModel):
    """Schéma pour la mise à jour des paramètres.
    Tous les champs sont optionnels pour permettre des mises à jour partielles.
    """
    platform_fee_percentage: Optional[float] = None
    maintenance_mode: Optional[bool] = None
    min_order_amount: Optional[int] = None
    max_order_amount: Optional[int] = None
    free_shipping_threshold: Optional[int] = None
    enable_notifications: Optional[bool] = None
    enable_two_factor: Optional[bool] = None
    orange_gateway_fee_percent: Optional[float] = None
    mtn_gateway_fee_percent: Optional[float] = None
    moov_gateway_fee_percent: Optional[float] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/", response_model=SettingsModel)
async def get_settings(  # ← Correction : async def
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Récupère les paramètres actuels de la plateforme.
    Si aucun document n'existe, retourne les valeurs par défaut.
    """
    doc = await db.settings.find_one({})
    if not doc:
        return SettingsModel()
    doc.pop("_id", None)
    return SettingsModel(**doc)


@router.put("/", response_model=SettingsModel)
async def update_settings(
    payload: SettingsUpdateRequest,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Met à jour les paramètres de la plateforme.
    Seuls les champs fournis sont modifiés (mise à jour partielle).
    Requiert les droits administrateur.
    """
    # Construire le dictionnaire de mise à jour avec les champs non vides
    update_doc: dict[str, Any] = {}
    for field, value in payload.dict(exclude_unset=True).items():
        if value is not None:
            update_doc[field] = value

    if not update_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucun champ à mettre à jour"
        )

    # Mettre à jour ou insérer le document unique
    await db.settings.update_one({}, {"$set": update_doc}, upsert=True)

    # Récupérer le document mis à jour
    updated_doc = await db.settings.find_one({})
    if updated_doc:
        updated_doc.pop("_id", None)
        return SettingsModel(**updated_doc)

    # En cas d'échec (peu probable), retourner les valeurs par défaut
    return SettingsModel()