import re
from typing import Dict, Any, List, Optional
from backend.app.utils.confidence import calculate_intent_confidence


class IntentClassifier:
    """Classifies user queries into remote sensing analysis intents."""

    # Intent routing rules
    GROUNDING_PATTERNS = [
        r"\bwhere is\b", r"\bwhere are\b", r"\blocate\b", r"\bhighlight\b",
        r"\bshow me where\b", r"\bfind the\b", r"\bsegment\b", r"\bbounding box\b",
        r"\bpinpoint\b", r"\bcoordinates of\b"
    ]

    CHANGE_DETECTION_PATTERNS = [
        r"\bwhat changed\b", r"\bchange between\b", r"\bcompare these\b",
        r"\bdifference between\b", r"\bwhat increased\b", r"\bwhat decreased\b",
        r"\btemporal change\b", r"\bbefore and after\b", r"\bdeforestation\b",
        r"\burban expansion\b", r"\bchanged\b"
    ]

    OPTICAL_SAR_PATTERNS = [
        r"\boptical and sar\b", r"\bsar and optical\b", r"\bradar and optical\b",
        r"\boptical and radar\b", r"\bcompare radar\b", r"\bmicrowave\b",
        r"\bbackscatter\b", r"\bsar analysis\b", r"\bsentinel-1 and sentinel-2\b"
    ]

    VQA_PATTERNS = [
        r"\bis there\b", r"\bare there\b", r"\bcan you see\b", r"\bdoes this contain\b",
        r"\bwhat crops\b", r"\bhow many\b", r"\bpresence of\b", r"\bexists\b",
        r"\bdo you find\b", r"\bwhat kind of crops\b", r"\bany water\b", r"\bany buildings\b"
    ]

    UNDERSTANDING_PATTERNS = [
        r"\bwhat is visible\b", r"\bdescribe\b", r"\bdescription\b",
        r"\boverview\b", r"\bwhat type of land\b", r"\bland cover\b",
        r"\bscene understanding\b", r"\btell me about this\b", r"\bsummarize\b"
    ]

    def classify(self, query: str, num_images: int = 1, image_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Determine intent taking into account query text, number of images, and metadata.
        Returns:
            intent: str ('image_understanding', 'vqa', 'grounding', 'change_detection', 'optical_sar')
            confidence: float
            reason: str
        """
        q = (query or "").lower().strip()
        matched_keywords = []

        # 1. Check Optical-SAR intent
        for pat in self.OPTICAL_SAR_PATTERNS:
            if re.search(pat, q):
                matched_keywords.append(pat)
                return {
                    "intent": "optical_sar",
                    "confidence": calculate_intent_confidence(q, matched_keywords, base_score=0.88),
                    "reason": "Question explicitly requests joint analysis or comparison of optical and radar (SAR) imagery."
                }

        # 2. Check Change Detection intent (strong if query words match OR 2 images with comparison wording)
        for pat in self.CHANGE_DETECTION_PATTERNS:
            if re.search(pat, q):
                matched_keywords.append(pat)
                return {
                    "intent": "change_detection",
                    "confidence": calculate_intent_confidence(q, matched_keywords, base_score=0.90),
                    "reason": "Question asks for comparison or difference detection across multitemporal acquisitions."
                }

        if num_images >= 2 and ("compare" in q or "difference" in q or "change" in q or "between" in q):
            return {
                "intent": "change_detection",
                "confidence": 0.88,
                "reason": "Multiple satellite acquisitions provided with multitemporal comparative intent."
            }

        # 3. Check Grounding intent ("Where is...", "Highlight...", "Locate...")
        for pat in self.GROUNDING_PATTERNS:
            if re.search(pat, q):
                matched_keywords.append(pat)
                return {
                    "intent": "grounding",
                    "confidence": calculate_intent_confidence(q, matched_keywords, base_score=0.89),
                    "reason": "User asked to locate, highlight, or bound a specific spatial feature in the image."
                }

        # 4. Check VQA intent ("Is there...", "Are there...", "What crops...")
        for pat in self.VQA_PATTERNS:
            if re.search(pat, q):
                matched_keywords.append(pat)
                return {
                    "intent": "vqa",
                    "confidence": calculate_intent_confidence(q, matched_keywords, base_score=0.86),
                    "reason": "Question asks whether a specific remote-sensing feature or entity is present."
                }

        # 5. Check Image Understanding intent ("What is visible...", "Describe...", "What type of land cover...")
        for pat in self.UNDERSTANDING_PATTERNS:
            if re.search(pat, q):
                matched_keywords.append(pat)
                return {
                    "intent": "image_understanding",
                    "confidence": calculate_intent_confidence(q, matched_keywords, base_score=0.87),
                    "reason": "User requested overall scene description and comprehensive land-cover characterization."
                }

        # Fallbacks based on question formulation
        if q.startswith("is ") or q.startswith("are ") or q.startswith("does ") or " crop" in q:
            return {
                "intent": "vqa",
                "confidence": 0.78,
                "reason": "Closed-ended question requiring verification of feature presence."
            }
        elif q.startswith("where") or "position" in q or "coordinate" in q:
            return {
                "intent": "grounding",
                "confidence": 0.80,
                "reason": "Spatial localization query."
            }
        else:
            return {
                "intent": "image_understanding",
                "confidence": 0.72,
                "reason": "General scene query defaulting to comprehensive remote sensing image understanding."
            }


intent_classifier = IntentClassifier()
