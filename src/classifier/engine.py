"""
Unified Classifier Engine for CyberRFP Maroc
Combines deterministic multi-lingual rules with optional Google AI Studio Gemini pass.
"""
from typing import Dict, List, Optional, Tuple, Any
from src.models import Tender
from src.classifier.rules import classify_text_rules
from src.classifier.llm_studio import GoogleStudioClassifier
from src.classifier.pdf_extractor import extract_document_text


class ClassifierEngine:
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.llm_classifier = GoogleStudioClassifier(api_key=gemini_api_key)

    def classify_tender(
        self,
        tender: Tender,
        document_path: Optional[str] = None
    ) -> Tender:
        """
        Classifies tender and updates its relevance_category, relevance_score,
        sub_category, summary, and matched_keywords.
        """
        # 1. Extract optional document text
        doc_text = ""
        if document_path:
            doc_text = extract_document_text(document_path, max_pages=3)

        # 2. Run deterministic rule-based classifier (always works standalone)
        category, score, subcat, keywords = classify_text_rules(
            title=tender.title,
            text_excerpt=doc_text
        )

        tender.relevance_category = category
        tender.relevance_score = score
        tender.sub_category = subcat
        tender.matched_keywords = keywords

        # Generate rule-based summary if none exists
        if keywords:
            tender.summary = f"Appel d'offres identifié par les mots-clés : {', '.join(keywords[:5])}."
        else:
            tender.summary = "Consultation générale ne présentant pas de marqueur cybersécurité explicite."

        # 3. Optional Google Studio Gemini Pass
        if self.llm_classifier.is_available:
            llm_result = self.llm_classifier.analyze_tender(
                title=tender.title,
                buyer_name=tender.buyer_name,
                procedure_type=tender.procedure_type,
                budget=tender.estimated_budget,
                caution=tender.provisional_guarantee or "",
                deadline=tender.deadline or "",
                text_excerpt=doc_text
            )
            if llm_result:
                # Combine or refine with LLM result
                tender.relevance_score = llm_result.get("relevance_score", tender.relevance_score)
                tender.relevance_category = llm_result.get("relevance_category", tender.relevance_category)
                tender.sub_category = llm_result.get("sub_category", tender.sub_category)
                if llm_result.get("summary_fr"):
                    tender.summary = llm_result["summary_fr"]

        return tender
