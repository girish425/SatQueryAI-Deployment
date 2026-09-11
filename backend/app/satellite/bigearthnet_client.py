import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger("satquery.bigearthnet")

BIGEARTHNET_CITATION = {
    "title": "BigEarthNet.txt: A Large-Scale Multi-Sensor Image-Text Dataset and Benchmark for Earth Observation",
    "arxiv_id": "2603.29630",
    "arxiv_url": "https://arxiv.org/abs/2603.29630",
    "official_website": "https://txt.bigearth.net",
    "authors": "Herzog, Adler, Hackel, Shu, Zavras, Papoutsis, Rota, Demir",
    "huggingface": "BIFOLD-BigEarthNetv2-0/BigEarthNet.txt",
    "total_pairs": 464044,
    "total_annotations": "9.6M text annotations"
}

BIGEARTHNET_DATASET: List[Dict[str, Any]] = [
    {
        "id": "BEN-MM-AUT-VALLEY-01",
        "title": "Alpine River Valley, Forest & Mixed Cultivation",
        "location": "Tyrol, Austria",
        "country": "Austria",
        "corine_labels": [
            "Broad-leaved forest",
            "Coniferous forest",
            "Water courses",
            "Complex cultivation patterns",
            "Discontinuous urban fabric"
        ],
        "sentinel2_file": "BigEarthNet_S2_patch_01_austria.tif",
        "sentinel1_file": "BigEarthNet_S1_patch_01_austria.tif",
        "s2_thumbnail": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=600&auto=format&fit=crop&q=80",
        "s1_thumbnail": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600&auto=format&fit=crop&q=80",
        "cloud_coverage": 0.0,
        "date": "2026-05-18",
        "resolution": "10m Multispectral / 10m C-SAR",
        "caption": "In the western sector, dense coniferous and broad-leaved forest covers the slopes. A sinuous water course traverses the central corridor, bordered on the east by complex agricultural cultivation patterns and a rural settlement in the southern section.",
        "vqa_pairs": [
            {
                "question": "Is there a water course traversing this patch?",
                "answer": "Yes, a distinct winding water course flows through the center of the patch, showing low radar backscatter and high optical absorption."
            },
            {
                "question": "What agricultural land cover is present?",
                "answer": "Complex cultivation patterns and managed pastures are visible in the eastern half."
            },
            {
                "question": "Are there buildings or urban fabric in the south?",
                "answer": "Yes, a discontinuous rural settlement with bright double-bounce radar response is located in the south."
            }
        ],
        "referring_expressions": [
            {"instruction": "Locate the water course in the center", "target": "river/water body"},
            {"instruction": "Highlight the forest canopy in the west", "target": "vegetation canopy"},
            {"instruction": "Find the discontinuous urban settlement in the south", "target": "built-up structures"}
        ]
    },
    {
        "id": "BEN-MM-MED-COAST-02",
        "title": "Mediterranean Coastal Lagoon & Permanent Olive Groves",
        "location": "Alentejo / Algarve, Portugal",
        "country": "Portugal",
        "corine_labels": [
            "Water bodies",
            "Coastal lagoons",
            "Sclerophyllous vegetation",
            "Permanent crops",
            "Olive groves"
        ],
        "sentinel2_file": "BigEarthNet_S2_patch_02_mediterranean.tif",
        "sentinel1_file": "BigEarthNet_S1_patch_02_mediterranean.tif",
        "s2_thumbnail": "https://images.unsplash.com/photo-1518457607834-6e8d80c183c5?w=600&auto=format&fit=crop&q=80",
        "s1_thumbnail": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600&auto=format&fit=crop&q=80",
        "cloud_coverage": 0.2,
        "date": "2026-06-24",
        "resolution": "10m MSI / 10m SAR",
        "caption": "A wide coastal lagoon and open water body dominates the southern quadrant, bordered by halophytic marshes and dry sandy shores. In the northern section, sclerophyllous scrubland transitions into managed olive groves and permanent agricultural orchards.",
        "vqa_pairs": [
            {
                "question": "Is there a coastal water body or lagoon present?",
                "answer": "Yes, a large calm water body occupies the southern quadrant, appearing dark in SAR due to specular reflection."
            },
            {
                "question": "What type of permanent crops are identified?",
                "answer": "Olive groves and sclerophyllous vegetation are present across the northern terrain."
            }
        ],
        "referring_expressions": [
            {"instruction": "Where is the coastal water body?", "target": "river/water body"},
            {"instruction": "Locate the olive groves and permanent crops", "target": "vegetation canopy"}
        ]
    },
    {
        "id": "BEN-MM-DEU-PORT-03",
        "title": "Harbor Waterway, Industrial Units & Urban Fabric",
        "location": "Hamburg Port, Germany",
        "country": "Germany",
        "corine_labels": [
            "Continuous urban fabric",
            "Industrial or commercial units",
            "Port areas",
            "Water bodies",
            "Transport units"
        ],
        "sentinel2_file": "BigEarthNet_S2_patch_03_port.tif",
        "sentinel1_file": "BigEarthNet_S1_patch_03_port.tif",
        "s2_thumbnail": "https://images.unsplash.com/photo-1524813686514-a57563d77d66?w=600&auto=format&fit=crop&q=80",
        "s1_thumbnail": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600&auto=format&fit=crop&q=80",
        "cloud_coverage": 0.8,
        "date": "2026-07-02",
        "resolution": "10m MSI / 10m SAR",
        "caption": "A navigable port basin and harbor waterway stretches across the western sector, accommodating maritime shipping berths. Expansive industrial and commercial logistics units with metallic roofs dominate the central sector, neighboring dense continuous urban fabric to the east.",
        "vqa_pairs": [
            {
                "question": "Are there industrial or commercial structures in this patch?",
                "answer": "Yes, extensive industrial facilities and warehouse units with high double-bounce radar returns occupy the central port sector."
            },
            {
                "question": "Is there water in the harbor?",
                "answer": "Yes, a navigable waterway basin extends through the western side."
            }
        ],
        "referring_expressions": [
            {"instruction": "Find the industrial units and metal warehouses", "target": "built-up structures"},
            {"instruction": "Highlight the harbor water channel", "target": "river/water body"}
        ]
    }
]


class BigEarthNetClient:
    """Client for querying BigEarthNet.txt (arXiv:2603.29630) co-registered dataset."""

    def __init__(self):
        self.citation = BIGEARTHNET_CITATION
        self.catalog = BIGEARTHNET_DATASET

    def search_patches(
        self,
        query: str = "",
        sensor_filter: Optional[str] = None,
        corine_label: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        q = (query or "").lower().strip()
        matched = []

        for patch in self.catalog:
            is_match = True

            if q:
                text_corpus = (
                    f"{patch['title']} {patch['location']} {patch['caption']} "
                    f"{' '.join(patch['corine_labels'])} "
                    f"{' '.join(p['question'] + ' ' + p['answer'] for p in patch['vqa_pairs'])}"
                ).lower()
                if q not in text_corpus:
                    is_match = False

            if corine_label and is_match:
                if not any(corine_label.lower() in cl.lower() for cl in patch["corine_labels"]):
                    is_match = False

            if is_match:
                matched.append(patch)

        if not matched:
            matched = self.catalog

        return matched[:limit]

    def get_patch_by_id(self, patch_id: str) -> Optional[Dict[str, Any]]:
        return next((p for p in self.catalog if p["id"] == patch_id), None)


bigearthnet_client = BigEarthNetClient()
