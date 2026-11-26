"""
Pydantic Models and Data Structures for CyberRFP Maroc
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class DocumentItem(BaseModel):
    title: str
    url: str
    doc_type: str = "DCE"  # DCE, Avis, Reglement, CPS, RC, etc.
    local_path: Optional[str] = None
    extracted_text: Optional[str] = None


class TenderChange(BaseModel):
    timestamp: str
    field_changed: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    change_type: str = "update"  # update, postponement, corrigendum, status_change


class Tender(BaseModel):
    id: str  # Unique generated hash or source_prefix:reference
    reference: str
    title: str
    buyer_name: str
    buyer_normalized: str = ""
    is_priority_buyer: bool = False
    priority_badge: Optional[str] = None
    
    procedure_type: str = "AOO"
    category: str = "Services"  # Services, Fournitures, Travaux
    lots: Optional[str] = None
    
    publication_date: Optional[str] = None
    deadline: Optional[str] = None  # Format: YYYY-MM-DD HH:MM:SS (Africa/Casablanca)
    bid_opening_date: Optional[str] = None
    bid_opening_place: Optional[str] = None
    
    estimated_budget: float = 0.0  # In Moroccan Dirhams (DH)
    provisional_guarantee: Optional[str] = None  # Caution provisoire (DH)
    qualifications: Optional[str] = None
    agrements: Optional[str] = None
    contact: Optional[str] = None
    
    source_name: str  # 'PMMP', 'Al Barid Bank', 'OFPPT', 'SOREC', 'Generic'
    source_url: str
    document_links: List[DocumentItem] = Field(default_factory=list)
    
    status: str = "open"  # 'open', 'amended', 'postponed', 'cancelled', 'awarded'
    relevance_category: str = "NOT_RELEVANT"  # 'CYBERSECURITY', 'MAYBE', 'NOT_RELEVANT'
    relevance_score: int = 0  # 0 to 100
    sub_category: Optional[str] = None
    summary: Optional[str] = None
    matched_keywords: List[str] = Field(default_factory=list)
    
    pipeline_status: str = "watching"  # 'watching', 'go', 'no_go', 'submitted', 'won', 'lost'
    pipeline_notes: str = ""
    
    dce_downloaded: bool = False  # Set to True when DPA downloads the DCE or consults the dossier
    dce_downloaded_at: Optional[str] = None
    alert_on_modification: bool = False  # Automatically set to True when DCE is downloaded; triggers PMMP alert if modified
    
    history: List[TenderChange] = Field(default_factory=list)
    first_seen_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ScraperHealth(BaseModel):
    connector_id: str
    name: str
    url: str
    status: str = "HEALTHY"  # HEALTHY, WARNING, ERROR, DISABLED
    last_run_time: Optional[str] = None
    last_success_time: Optional[str] = None
    items_found_last_run: int = 0
    total_items_indexed: int = 0
    error_message: Optional[str] = None


class WatchlistBuyer(BaseModel):
    name: str
    normalized_keywords: List[str]
    badge_label: str
    category: str = "Établissement Public"
    notes: Optional[str] = None


class User(BaseModel):
    id: str
    email: str
    full_name: str
    role: str = "Consultant Cybersécurité"
    is_active: bool = True
    is_admin: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_login: Optional[str] = None


class UserRegister(BaseModel):
    email: str
    full_name: str
    role: str = "Consultant Cybersécurité"
    password: Optional[str] = None
    send_password_by_email: bool = True


class UserLogin(BaseModel):
    email: str
    password: str
    remember_me: bool = True


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetSubmit(BaseModel):
    token: str
    new_password: str


class FirstLoginPasswordChange(BaseModel):
    email: str
    temp_password: str
    new_password: str


