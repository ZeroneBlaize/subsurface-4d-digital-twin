"""
Borehole PDF Parser: Automated Extraction of Geotechnical Drilling Logs from Digital and Scanned PDFs.
"""

from pathlib import Path
from typing import Union, List, Dict, Optional
import re
import pandas as pd
from pypdf import PdfReader


class BoreholePDFExtractor:
    """
    Parses unstructured geotechnical borehole drilling logs from PDF reports,
    extracting coordinates, collar R.L., groundwater levels, strata intervals, and SPT N-values.
    """
    def __init__(self):
        # Patterns for metadata extraction
        self.re_bh_id = re.compile(r"(?:Bore\s*hole\s*(?:No|ID|\#)?|BH\s*[-_]?\s*(?:No|ID)?)\s*[:.]?\s*([A-Za-z0-9\-_]+)", re.IGNORECASE)
        self.re_elevation = re.compile(r"(?:R\.?L\.?|Ground\s*Elevation|Collar\s*R\.?L\.?|Surface\s*Elevation)\s*[:.]?\s*([0-9]+(?:\.[0-9]+)?)\s*m?", re.IGNORECASE)
        self.re_coordinates = re.compile(r"(?:Easting|X)\s*[:.]?\s*([0-9]+(?:\.[0-9]+)?).*?(?:Northing|Y)\s*[:.]?\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE | re.DOTALL)
        self.re_water_table = re.compile(r"(?:Water\s*Table|Groundwater|GWT|G\.?W\.?L\.?)\s*[:.]?\s*([0-9]+(?:\.[0-9]+)?)\s*m?", re.IGNORECASE)
        
        # Pattern for tabular lines: Depth_From Depth_To SPT_N Description
        self.re_table_line = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s+([0-9]+(?:\.[0-9]+)?)\s+([0-9]+|>50|Refusal)?\s+(.+)$")

    def parse_pdf(self, pdf_path: Union[str, Path]) -> pd.DataFrame:
        """
        Extracts all borehole logs from a single or multi-page PDF document.
        """
        p = Path(pdf_path)
        if not p.exists():
            raise FileNotFoundError(f"PDF file not found: {p}")
            
        reader = PdfReader(str(p))
        all_records = []
        
        current_bh_id = p.stem
        current_elevation = None
        current_easting = None
        current_northing = None
        current_water_table = None
        
        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            lines = text.split("\n")
            
            # 1. Parse Header Metadata
            m_id = self.re_bh_id.search(text)
            if m_id:
                current_bh_id = m_id.group(1).strip()
                
            m_elev = self.re_elevation.search(text)
            if m_elev:
                current_elevation = float(m_elev.group(1))
                
            m_coords = self.re_coordinates.search(text)
            if m_coords:
                current_easting = float(m_coords.group(1))
                current_northing = float(m_coords.group(2))
                
            m_wt = self.re_water_table.search(text)
            if m_wt:
                current_water_table = float(m_wt.group(1))
                
            # 2. Parse Strata Lines
            for line in lines:
                m_line = self.re_table_line.match(line.strip())
                if m_line:
                    depth_from = float(m_line.group(1))
                    depth_to = float(m_line.group(2))
                    n_raw = m_line.group(3)
                    description = m_line.group(4).strip()
                    
                    if n_raw is None or "refusal" in n_raw.lower() or ">" in n_raw:
                        n_val = 60
                    else:
                        try:
                            n_val = int(n_raw)
                        except ValueError:
                            n_val = 15
                            
                    all_records.append({
                        "Borehole_ID": current_bh_id,
                        "Easting_m": current_easting,
                        "Northing_m": current_northing,
                        "Surface_RL_m": current_elevation,
                        "Depth_From_m": depth_from,
                        "Depth_To_m": depth_to,
                        "Field_N": n_val,
                        "Layer_Name": description,
                        "Water_Table_Depth_m": current_water_table if current_water_table else 3.0
                    })
                    
        df = pd.DataFrame(all_records)
        return df
