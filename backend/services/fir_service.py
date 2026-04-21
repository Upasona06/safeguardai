"""
FIR Service — generates court-ready PDF using ReportLab Platypus,
uploads to Cloudinary, and persists metadata.
"""

import asyncio
import logging
import os
import uuid
from datetime import datetime, timedelta
from datetime import timezone
from pathlib import Path
from urllib.parse import urlparse
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.platypus.flowables import HRFlowable

from backend.config.settings import settings
from backend.models.schemas import FinalizeFIRRequest
from backend.services.cloudinary_service import CloudinaryService

logger = logging.getLogger(__name__)

_EPHEMERAL_FIR_DOWNLOADS: dict[str, tuple[str | None, str | None]] = {}
_EPHEMERAL_FIR_RECORDS: dict[str, dict] = {}


def get_ist_now():
    """Get current time in IST (UTC+5:30)"""
    ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    return ist


def convert_to_ist(utc_dt: datetime) -> datetime:
    """Convert UTC datetime to IST"""
    return utc_dt + timedelta(hours=5, minutes=30)


class FIRService:
    def __init__(self, db):
        self.db = db
        self.output_dir = Path(settings.FIR_OUTPUT_DIR)

    def _ensure_output_dir(self) -> Path:
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            fallback_dir = Path("/tmp/fir_pdfs")
            fallback_dir.mkdir(parents=True, exist_ok=True)
            logger.warning(
                "FIR_OUTPUT_DIR '%s' unavailable (%s). Falling back to '%s'.",
                self.output_dir,
                e,
                fallback_dir,
            )
            self.output_dir = fallback_dir
        return self.output_dir

    @staticmethod
    def _new_fir_id() -> str:
        return f"FIR-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def _normalize_user_scope(
        user_id: str | None,
        user_email: str | None,
    ) -> tuple[str | None, str | None]:
        normalized_id = (user_id or "").strip() or None
        normalized_email = (user_email or "").strip().lower() or None
        return normalized_id, normalized_email

    @staticmethod
    def _owner_filter(user_id: str | None, user_email: str | None) -> dict | None:
        conditions = []
        if user_id:
            conditions.append({"owner_user_id": user_id})
        if user_email:
            conditions.append({"owner_email": user_email})

        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$or": conditions}

    @staticmethod
    def _record_matches_owner(record: dict, user_id: str | None, user_email: str | None) -> bool:
        owner_user_id = record.get("owner_user_id")
        owner_email_raw = record.get("owner_email")
        owner_email = owner_email_raw.lower() if isinstance(owner_email_raw, str) else owner_email_raw
        return bool(
            (user_id and owner_user_id == user_id)
            or (user_email and owner_email == user_email)
        )

    @staticmethod
    def _cloudinary_public_id_candidates(fir_id: str, pdf_url: str | None) -> list[str]:
        """Derive likely Cloudinary raw public_id values for signed download."""
        candidates: list[str] = []

        if pdf_url and "res.cloudinary.com" in pdf_url:
            try:
                path = urlparse(str(pdf_url)).path
                marker = "/raw/upload/"
                if marker in path:
                    tail = path.split(marker, 1)[1].lstrip("/")
                    parts = [p for p in tail.split("/") if p]

                    # Strip Cloudinary version segment, e.g. v1776713217
                    if parts and parts[0].startswith("v") and parts[0][1:].isdigit():
                        parts = parts[1:]

                    parsed_public_id = "/".join(parts)
                    if parsed_public_id:
                        candidates.append(parsed_public_id)
                        if parsed_public_id.lower().endswith(".pdf"):
                            candidates.append(parsed_public_id[:-4])
                        else:
                            candidates.append(f"{parsed_public_id}.pdf")
            except Exception:
                # Keep fallback candidates below.
                pass

        # Fallback patterns used across historical uploads.
        candidates.extend([
            f"fir_reports/{fir_id}.pdf",
            f"fir_reports/{fir_id}",
            f"{fir_id}.pdf",
            fir_id,
        ])

        seen: set[str] = set()
        ordered: list[str] = []
        for candidate in candidates:
            if candidate and candidate not in seen:
                seen.add(candidate)
                ordered.append(candidate)
        return ordered

    def _prefer_signed_cloudinary_url(self, fir_id: str, pdf_url: str | None) -> str | None:
        if not pdf_url or "res.cloudinary.com" not in str(pdf_url):
            return pdf_url

        cloudinary_service = CloudinaryService()
        candidates = self._cloudinary_public_id_candidates(fir_id, str(pdf_url))

        validated_candidates = [
            candidate
            for candidate in candidates
            if cloudinary_service.raw_resource_exists(candidate)
        ]

        # Prefer known-existing resources; fall back to heuristic order if lookup fails.
        for public_id in (validated_candidates or candidates):
            signed_url = cloudinary_service.build_signed_raw_download_url(
                public_id=public_id,
                filename=f"FIR_{fir_id}.pdf",
            )
            if signed_url:
                return signed_url

        return pdf_url

                                                                    
    async def create_fir_record(
        self,
        analysis_id: str,
        user_id: str | None = None,
        user_email: str | None = None,
    ) -> str:
        user_id, user_email = self._normalize_user_scope(user_id, user_email)
        if not user_id and not user_email:
            raise ValueError("User identity required")

        if self.db is None:
            fir_id = self._new_fir_id()
            _EPHEMERAL_FIR_RECORDS[fir_id] = {
                "fir_id": fir_id,
                "analysis_id": analysis_id,
                "owner_user_id": user_id,
                "owner_email": user_email,
                "status": "draft",
                "created_at": datetime.utcnow(),
                "pdf_path": None,
                "pdf_url": None,
                "complainant_name": "—",
                "incident_date": "—",
            }
            logger.warning(
                "MongoDB unavailable; generating ephemeral FIR id without persistence: %s",
                fir_id,
            )
            return fir_id

        analysis = None
        # Analysis persistence can be asynchronous; wait briefly before degrading.
        for _ in range(4):
            analysis = await self.db.analyses.find_one({"id": analysis_id})
            if analysis:
                break
            await asyncio.sleep(0.25)

        fir_id = self._new_fir_id()

        await self.db.fir_reports.insert_one({
            "fir_id": fir_id,
            "analysis_id": analysis_id,
            "owner_user_id": user_id,
            "owner_email": user_email,
            "status": "draft",
            "analysis_found": bool(analysis),
            "created_at": datetime.utcnow(),
            "pdf_path": None,
            "pdf_url": None,
        })
        if not analysis:
            logger.warning(
                "Analysis %s not found after retry; created FIR %s in degraded mode",
                analysis_id,
                fir_id,
            )
        logger.info("FIR record created: %s", fir_id)
        return fir_id

                                                                    
    async def generate_fir_pdf(
        self,
        data: FinalizeFIRRequest,
        user_id: str | None = None,
        user_email: str | None = None,
    ) -> str:
        user_id, user_email = self._normalize_user_scope(user_id, user_email)
        owner_filter = self._owner_filter(user_id, user_email)
        if owner_filter is None:
            raise ValueError("User identity required")

        fir_record = None
        analysis = None
        now_utc = datetime.utcnow()
        if self.db is not None:
            fir_record = await self.db.fir_reports.find_one({"fir_id": data.fir_id, **owner_filter})
            if not fir_record:
                raise ValueError(f"FIR {data.fir_id} not found")
            # Analysis persistence is async after /analyze-*; retry briefly to avoid "N/A" content in FIR.
            for _ in range(4):
                analysis = await self.db.analyses.find_one({"id": data.analysis_id})
                if analysis:
                    break
                await asyncio.sleep(0.25)
        else:
            logger.warning("MongoDB unavailable; finalizing FIR in non-persistent mode")

        output_dir = self._ensure_output_dir()
        pdf_path = output_dir / f"{data.fir_id}.pdf"
        self._build_pdf(pdf_path, data, analysis)

                              
        cloudinary = CloudinaryService()
        pdf_url = await cloudinary.upload_file(
            str(pdf_path),
            folder="fir_reports",
            resource_type="raw",
            public_id=data.fir_id,
        )

        _EPHEMERAL_FIR_DOWNLOADS[data.fir_id] = (str(pdf_path), pdf_url or None)
        _EPHEMERAL_FIR_RECORDS.setdefault(
            data.fir_id,
            {
                "fir_id": data.fir_id,
                "analysis_id": data.analysis_id,
                "owner_user_id": user_id,
                "owner_email": user_email,
                "created_at": now_utc,
            },
        )
        _EPHEMERAL_FIR_RECORDS[data.fir_id].update({
            "status": "finalized",
            "analysis_id": data.analysis_id,
            "owner_user_id": user_id,
            "owner_email": user_email,
            "pdf_path": str(pdf_path),
            "pdf_url": pdf_url,
            "complainant_name": data.complainant_name,
            "complainant_contact": data.complainant_contact,
            "complainant_address": data.complainant_address,
            "accused_name": data.accused_name,
            "accused_details": data.accused_details,
            "incident_date": data.incident_date,
            "incident_time": data.incident_time,
            "incident_location": data.incident_location,
            "finalized_at": now_utc,
        })

        if self.db is not None:
            created_at_value = (
                fir_record.get("created_at")
                if fir_record and fir_record.get("created_at")
                else _EPHEMERAL_FIR_RECORDS[data.fir_id].get("created_at", now_utc)
            )
            await self.db.fir_reports.update_one(
                {"fir_id": data.fir_id, **owner_filter},
                {
                    "$set": {
                        "status": "finalized",
                        "analysis_id": data.analysis_id,
                        "owner_user_id": user_id,
                        "owner_email": user_email,
                        "pdf_path": str(pdf_path),
                        "pdf_url": pdf_url,
                        "complainant_name": data.complainant_name,
                        "complainant_contact": data.complainant_contact,
                        "complainant_address": data.complainant_address,
                        "accused_name": data.accused_name,
                        "accused_details": data.accused_details,
                        "incident_date": data.incident_date,
                        "incident_time": data.incident_time,
                        "incident_location": data.incident_location,
                        "finalized_at": now_utc,
                    },
                    "$setOnInsert": {
                        "created_at": created_at_value,
                    },
                },
                upsert=True,
            )
        logger.info("FIR finalized: %s → %s", data.fir_id, pdf_url)
        return pdf_url

    async def _sync_ephemeral_records_to_db(self) -> None:
        if self.db is None or not _EPHEMERAL_FIR_RECORDS:
            return

        for fir_id, record in list(_EPHEMERAL_FIR_RECORDS.items()):
            try:
                created_at_value = record.get("created_at") or datetime.utcnow()
                await self.db.fir_reports.update_one(
                    {"fir_id": fir_id},
                    {
                        "$set": {
                            "status": record.get("status", "draft"),
                            "analysis_id": record.get("analysis_id"),
                            "owner_user_id": record.get("owner_user_id"),
                            "owner_email": record.get("owner_email"),
                            "pdf_path": record.get("pdf_path"),
                            "pdf_url": record.get("pdf_url"),
                            "complainant_name": record.get("complainant_name"),
                            "complainant_contact": record.get("complainant_contact"),
                            "complainant_address": record.get("complainant_address"),
                            "accused_name": record.get("accused_name"),
                            "accused_details": record.get("accused_details"),
                            "incident_date": record.get("incident_date"),
                            "incident_time": record.get("incident_time"),
                            "incident_location": record.get("incident_location"),
                            "finalized_at": record.get("finalized_at"),
                        },
                        "$setOnInsert": {
                            "created_at": created_at_value,
                        },
                    },
                    upsert=True,
                )
            except Exception as e:
                logger.warning("Failed to sync ephemeral FIR %s: %s", fir_id, e)

                                                                    
    async def get_fir_pdf_path(self, fir_id: str) -> str:
        if self.db is None:
            raise ValueError("FIR download requires database persistence")
        record = await self.db.fir_reports.find_one({"fir_id": fir_id})
        if not record or not record.get("pdf_path"):
            raise ValueError(f"PDF for FIR {fir_id} not ready")
        return record["pdf_path"]

    async def get_fir_download_targets(
        self,
        fir_id: str,
        user_id: str | None = None,
        user_email: str | None = None,
    ) -> tuple[str | None, str | None]:
        """Return local PDF path and cloud URL for download fallback handling."""
        user_id, user_email = self._normalize_user_scope(user_id, user_email)
        owner_filter = self._owner_filter(user_id, user_email)
        if owner_filter is None:
            raise ValueError("User identity required")

        if self.db is None:
            ephemeral_record = _EPHEMERAL_FIR_RECORDS.get(fir_id)
            if not ephemeral_record or not self._record_matches_owner(ephemeral_record, user_id, user_email):
                raise ValueError(f"FIR {fir_id} not found")

            cached = _EPHEMERAL_FIR_DOWNLOADS.get(fir_id)
            if cached:
                pdf_path, pdf_url = cached
                pdf_url = self._prefer_signed_cloudinary_url(fir_id, pdf_url)
                return pdf_path, pdf_url

            local_path = str(self._ensure_output_dir() / f"{fir_id}.pdf")
            if os.path.exists(local_path):
                return local_path, None

            raise ValueError("FIR download not available in non-persistent mode")
        record = await self.db.fir_reports.find_one({"fir_id": fir_id, **owner_filter})
        if not record:
            cached = _EPHEMERAL_FIR_DOWNLOADS.get(fir_id)
            ephemeral_record = _EPHEMERAL_FIR_RECORDS.get(fir_id)
            if cached and ephemeral_record and self._record_matches_owner(ephemeral_record, user_id, user_email):
                pdf_path, pdf_url = cached
                pdf_url = self._prefer_signed_cloudinary_url(fir_id, pdf_url)
                return pdf_path, pdf_url
            raise ValueError(f"FIR {fir_id} not found")

        pdf_path = record.get("pdf_path")
        pdf_url = record.get("pdf_url")

        # Prefer signed Cloudinary URL to avoid 401 on raw PDF delivery.
        pdf_url = self._prefer_signed_cloudinary_url(fir_id, pdf_url)

        if not pdf_path and not pdf_url:
            raise ValueError(f"PDF for FIR {fir_id} not ready")

        return pdf_path, pdf_url

                                                                   
    async def get_fir_history(
        self,
        limit: int = 50,
        skip: int = 0,
        user_id: str | None = None,
        user_email: str | None = None,
    ):
        """Fetch FIR history sorted by creation date (newest first)"""
        user_id, user_email = self._normalize_user_scope(user_id, user_email)
        owner_filter = self._owner_filter(user_id, user_email)
        if owner_filter is None:
            raise ValueError("User identity required")

        limit = max(1, min(limit, 100))
        skip = max(0, skip)

        if self.db is None:
            records = sorted(
                [
                    item
                    for item in _EPHEMERAL_FIR_RECORDS.values()
                    if self._record_matches_owner(item, user_id, user_email)
                ],
                key=lambda item: item.get("created_at") or datetime.min,
                reverse=True,
            )
            page = records[skip: skip + limit]
            history_items = []
            for fir in page:
                incident_date = fir.get("incident_date")
                if isinstance(incident_date, datetime):
                    incident_date = incident_date.date().isoformat()
                elif incident_date is None:
                    incident_date = "—"

                history_items.append({
                    "fir_id": str(fir.get("fir_id") or ""),
                    "status": str(fir.get("status", "draft")),
                    "complainant_name": str(fir.get("complainant_name") or "—"),
                    "accused_name": str(fir.get("accused_name")) if fir.get("accused_name") else None,
                    "incident_date": str(incident_date),
                    "incident_location": str(fir.get("incident_location")) if fir.get("incident_location") else None,
                    "created_at": fir.get("created_at") or datetime.utcnow(),
                    "finalized_at": fir.get("finalized_at"),
                    "pdf_url": str(fir.get("pdf_url")) if fir.get("pdf_url") else None,
                })

            return {"firs": history_items, "total": len(records)}

        await self._sync_ephemeral_records_to_db()

        projection = {
            "_id": 0,
            "fir_id": 1,
            "status": 1,
            "complainant_name": 1,
            "accused_name": 1,
            "incident_date": 1,
            "incident_location": 1,
            "created_at": 1,
            "finalized_at": 1,
            "pdf_url": 1,
        }

        async def _fetch_page() -> list[dict]:
            cursor = (
                self.db.fir_reports.find(owner_filter, projection)
                .sort([
                    ("created_at", -1),
                    ("finalized_at", -1),
                    ("fir_id", -1),
                ])
                .skip(skip)
                .limit(limit)
            )
            return await cursor.to_list(length=limit)

        async def _fetch_total() -> int:
            return await self.db.fir_reports.count_documents(owner_filter)

        try:
            firs, total = await asyncio.gather(_fetch_page(), _fetch_total())
        except Exception as e:
            logger.warning("Primary FIR history query failed; using fallback query: %s", e)
            firs = await (
                self.db.fir_reports.find(owner_filter, projection)
                .sort("fir_id", -1)
                .skip(skip)
                .limit(limit)
                .to_list(length=limit)
            )
            total = await self.db.fir_reports.count_documents(owner_filter)

        def _to_datetime(value):
            if isinstance(value, datetime):
                return value
            if value is None:
                return None
            if isinstance(value, (int, float)):
                try:
                    return datetime.fromtimestamp(value, tz=timezone.utc)
                except Exception:
                    return None
            if isinstance(value, str):
                text = value.strip()
                if not text:
                    return None
                try:
                    return datetime.fromisoformat(text.replace("Z", "+00:00"))
                except Exception:
                    return None
            return None
        
                                    
        history_items = []
        for fir in firs:
            try:
                created_at = (
                    _to_datetime(fir.get("created_at"))
                    or _to_datetime(fir.get("finalized_at"))
                    or datetime.utcnow()
                )
                finalized_at = _to_datetime(fir.get("finalized_at"))
                incident_date = fir.get("incident_date")
                if isinstance(incident_date, datetime):
                    incident_date = incident_date.date().isoformat()
                elif incident_date is None:
                    incident_date = "—"

                history_items.append({
                    "fir_id": str(fir.get("fir_id") or ""),
                    "status": str(fir.get("status", "draft")),
                    "complainant_name": str(fir.get("complainant_name") or "—"),
                    "accused_name": str(fir.get("accused_name")) if fir.get("accused_name") else None,
                    "incident_date": str(incident_date),
                    "incident_location": str(fir.get("incident_location")) if fir.get("incident_location") else None,
                    "created_at": created_at,
                    "finalized_at": finalized_at,
                    "pdf_url": str(fir.get("pdf_url")) if fir.get("pdf_url") else None,
                })
            except Exception as item_error:
                logger.warning("Skipping malformed FIR history record: %s", item_error)
        
        return {"firs": history_items, "total": total}

                                                                    
    def _build_pdf(
        self,
        pdf_path: Path,
        data: FinalizeFIRRequest,
        analysis: dict | None,
    ) -> None:
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()
        story = []

                                                                    
        title_style = ParagraphStyle(
            "FIRTitle",
            fontSize=16,
            fontName="Helvetica-Bold",
            alignment=TA_CENTER,
            spaceAfter=6,
            textColor=colors.HexColor("#1a1a2e"),
        )
        subtitle_style = ParagraphStyle(
            "FIRSubtitle",
            fontSize=11,
            fontName="Helvetica",
            alignment=TA_CENTER,
            spaceAfter=4,
            textColor=colors.HexColor("#4a4a6a"),
        )
        section_style = ParagraphStyle(
            "Section",
            fontSize=10,
            fontName="Helvetica-Bold",
            spaceBefore=12,
            spaceAfter=4,
            textColor=colors.HexColor("#c0392b"),
            borderPad=4,
        )
        body_style = ParagraphStyle(
            "Body",
            fontSize=9,
            fontName="Helvetica",
            leading=14,
            alignment=TA_JUSTIFY,
            textColor=colors.HexColor("#2c2c2c"),
        )
        mono_style = ParagraphStyle(
            "Mono",
            fontSize=8,
            fontName="Courier",
            textColor=colors.HexColor("#555555"),
            leading=12,
        )

                                                                    
        story.append(Paragraph("FIRST INFORMATION REPORT (FIR)", title_style))
        story.append(Paragraph("Under the Information Technology Act, 2000 & Indian Penal Code", subtitle_style))
        story.append(Paragraph("Generated by SafeGuard AI Platform", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#c0392b")))
        story.append(Spacer(1, 0.4 * cm))

                                                                    
        ist_now = get_ist_now()
        meta_data = [
            ["FIR Number:", data.fir_id, "Date:", ist_now.strftime("%d %B %Y")],
            ["Time of Filing:", ist_now.strftime("%H:%M IST"), "Case ID:", data.analysis_id[:16] + "..."],
        ]
        meta_table = Table(meta_data, colWidths=[3.5 * cm, 6 * cm, 3.5 * cm, 4 * cm])
        meta_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f8f8f8"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 0.5 * cm))

                                                                    
        story.append(Paragraph("1. COMPLAINANT DETAILS", section_style))
        comp_data = [
            ["Name:", data.complainant_name],
            ["Contact:", data.complainant_contact],
        ]
        if data.complainant_address:
            comp_data.append(["Address:", data.complainant_address])
        
        comp_table = Table(comp_data, colWidths=[4 * cm, 13 * cm])
        comp_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#eeeeee")),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(comp_table)
        
                                                                    
        if data.accused_name or data.accused_details:
            story.append(Spacer(1, 0.3 * cm))
            story.append(Paragraph("2. AGAINST WHOM (ACCUSED/RESPONDENT)", section_style))
            accused_data = []
            if data.accused_name:
                accused_data.append(["Name/Account:", data.accused_name])
            if data.accused_details:
                accused_data.append(["Username/Profile:", data.accused_details])
            
            if accused_data:
                accused_table = Table(accused_data, colWidths=[4 * cm, 13 * cm])
                accused_table.setStyle(TableStyle([
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#eeeeee")),
                    ("PADDING", (0, 0), (-1, -1), 6),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))
                story.append(accused_table)
            section_num = 3
        else:
            section_num = 2

                                                                   
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"{section_num}. INCIDENT DETAILS", section_style))
        incident_data = [
            ["Date:", data.incident_date],
            ["Time (IST):", data.incident_time or "Not Specified"],
            ["Location:", data.incident_location or "Online Platform"],
        ]
        incident_table = Table(incident_data, colWidths=[4 * cm, 13 * cm])
        incident_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#eeeeee")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(incident_table)

                                                                    
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"{section_num + 1}. AI ANALYSIS SUMMARY", section_style))

        if analysis:
            risk = analysis.get("risk_level", "UNKNOWN")
            risk_color = {
                "LOW": "#27ae60", "MEDIUM": "#f39c12",
                "HIGH": "#e67e22", "CRITICAL": "#c0392b"
            }.get(risk, "#888888")

            ai_data = [
                ["Risk Level:", risk, "Overall Score:", f"{analysis.get('overall_score', 0)*100:.1f}%"],
                ["Language:", analysis.get("language_detected", "Unknown"), "Timestamp:", str(analysis.get("timestamp", ""))[:19]],
            ]
            ai_table = Table(ai_data, colWidths=[3.5 * cm, 6 * cm, 3.5 * cm, 4 * cm])
            ai_table.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
                ("TEXTCOLOR", (1, 0), (1, 0), colors.HexColor(risk_color)),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(ai_table)
            story.append(Spacer(1, 0.2 * cm))

                             
            labels = analysis.get("labels", {})
            if labels:
                scores_data = [["Category", "Score", "Category", "Score"]]
                items = list(labels.items())
                for i in range(0, len(items), 2):
                    row = [items[i][0].replace("_", " ").title(), f"{items[i][1]*100:.1f}%"]
                    if i + 1 < len(items):
                        row += [items[i+1][0].replace("_", " ").title(), f"{items[i+1][1]*100:.1f}%"]
                    else:
                        row += ["—", "—"]
                    scores_data.append(row)

                scores_table = Table(scores_data, colWidths=[5 * cm, 3 * cm, 5 * cm, 3 * cm])
                scores_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#c0392b")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#fef9f9"), colors.white]),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ]))
                story.append(scores_table)

                                                                    
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"{section_num + 2}. INCIDENT DESCRIPTION & EVIDENCE", section_style))

        analysis_text = ""
        if analysis is not None:
            analysis_text = str(analysis.get("original_text") or "").strip()
            if analysis_text.upper() == "N/A":
                analysis_text = ""

        user_incident_description = str(data.additional_info or "").strip()
        incident_description = analysis_text or user_incident_description or "N/A"

        story.append(Paragraph(
            f"The following content was submitted for analysis and flagged as harmful:<br/><br/>"
            f'<font name="Courier" size="8" color="#555555">"{escape(incident_description[:800])}"</font>',
            body_style
        ))

        if user_incident_description and user_incident_description != incident_description:
            story.append(Spacer(1, 0.2 * cm))
            story.append(Paragraph("<b>Complainant's Description of Incident:</b>", body_style))
            story.append(Paragraph(escape(user_incident_description), body_style))

                                                                    
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"{section_num + 3}. APPLICABLE LEGAL PROVISIONS", section_style))

        if data.legal_sections:
            legal_data = [["#", "Legal Section / Provision"]]
            for i, section in enumerate(data.legal_sections, 1):
                legal_data.append([str(i), section])

            legal_table = Table(legal_data, colWidths=[1 * cm, 16 * cm])
            legal_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0f4f8"), colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(legal_table)
        else:
            story.append(Paragraph("No specific legal sections mapped.", body_style))

                                                                    
        if data.evidence_urls:
            story.append(Spacer(1, 0.3 * cm))
            story.append(Paragraph(f"{section_num + 4}. DIGITAL EVIDENCE / SUPPORTING DOCUMENTS", section_style))
            for i, url in enumerate(data.evidence_urls, 1):
                story.append(Paragraph(f"{i}. {url}", mono_style))

                                                                    
        if analysis and analysis.get("explanation"):
            story.append(Spacer(1, 0.3 * cm))
            story.append(Paragraph(f"{section_num + 5}. AI REASONING & EXPLAINABILITY", section_style))
            story.append(Paragraph(analysis["explanation"], body_style))

                                                                    
        story.append(Spacer(1, 0.5 * cm))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(
            "DECLARATION: I, the complainant, hereby declare that the information provided above is "
            "true and correct to the best of my knowledge. This FIR has been generated using the "
            "SafeGuard AI platform with AI-assisted evidence analysis. The AI analysis is provided "
            "as supporting evidence and does not substitute for official law enforcement investigation.",
            ParagraphStyle("Decl", fontSize=7, fontName="Helvetica", alignment=TA_JUSTIFY,
                           textColor=colors.HexColor("#666666"), leading=11)
        ))
        story.append(Spacer(1, 0.8 * cm))

                        
        sig_data = [
            [data.complainant_name, "", data.incident_date],
            ["Complainant Signature", "", "Date"],
        ]
        sig_table = Table(sig_data, colWidths=[7 * cm, 3 * cm, 7 * cm])
        sig_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica"),
            ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("LINEBELOW", (0, 0), (0, 0), 1, colors.black),
            ("LINEBELOW", (2, 0), (2, 0), 1, colors.black),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(sig_table)

                     
        story.append(Spacer(1, 0.5 * cm))
        ist_now = get_ist_now()
        story.append(Paragraph(
            f"Generated by SafeGuard AI | FIR ID: {data.fir_id} | {ist_now.strftime('%Y-%m-%d %H:%M IST')}",
            ParagraphStyle("Footer", fontSize=6, fontName="Helvetica",
                           alignment=TA_CENTER, textColor=colors.HexColor("#aaaaaa"))
        ))

        doc.build(story)
        logger.info("PDF built: %s", pdf_path)
