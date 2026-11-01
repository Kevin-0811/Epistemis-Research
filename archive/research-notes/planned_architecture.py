"""
🔷 FULL SYSTEM ARCHITECTURE (CURRENT DESIGN)
 This is your end-to-end pipeline, from raw paper → final flags
 1. PREPROCESSOR (you already built this)
 Input: PDF / text
 Output: Structured sentences with: 
 { sentence, sentence_id, 
   epistemic_mode, # E0-E3 excluded and noise filtering 
   anchors, # A1-A6 
   has_anchor, 
   linked_anchor, 
   anchor_distance, # (optional but useful) 
   } 
  Key responsibilities: 
  ✔ Structural filtering Remove metadata, math-heavy, low-signal text 
  ✔ Epistemic gating Keep only E2 / E3 for downstream 
  ✔ Anchoring signal Detect context presence (explicit + local linking) 
  Output constraint: Only pass forward sentences where: epistemic_mode in {E2, E3} and not excluded 
  
  2. WINDOWING LAYER 
  Input: sentence stream 
  Output: { window_text, sentences: [6 sentences], metadata per sentence } 
  Purpose: Provide local context for models Maintain discourse coherence 
  
  3. STAGE 1 — DistilBERT (TRIAGE MODEL) 
  Role: Fast decision filter (certainty + direction) 
  Input: sentence_id +1 and -1
  Output: { label: "CLEAN" | "F1" | "F2" | "UNCERTAIN", confidence: float } 
  Behavior: ✔ CLEAN (high confidence) → discard 
            ✔ F1 / F2 (high confidence) → direct flag → skip SciBERT 
            ✔ UNCERTAIN OR low confidence → send to SciBERT 
  Constraints: Only obvious F1/F2 allowed 
               NO F3 detection here 
               Must be high recall, moderate precision 
               
4. ROUTING LOGIC (CRITICAL CONTROL LAYER) 
if label == "CLEAN" and confidence > T_high: discard 
elif label in {"F1", "F2"} and confidence > T_high: return label # final output 
else: send to SciBERT 
Typical thresholds: T_high ≈ 0.85-0.95. 

STAGE 2 — SciBERT (PRECISION MODEL) 
Role: Accurate classifier for hard cases 
Input: UNCERTAIN / low-confidence windows 
Output: { label: "F1" | "F2" | "F3" | "NONE", confidence: float } 
Responsibilities: Distinguish F1 vs F2 vs F3 Detect missing context (F3) 
                  Handle: weak anchoring, borderline claims, nuanced language 
Constraints: High precision
             Lower recall acceptable
             Trained on clean dataset
              
 6. FINAL DECISION LAYER 
 Combine outputs: if from DistilBERT (high confidence F1/F2): accept 
                  elif from SciBERT: if confidence > threshold: accept 
                  else: discard 
                  
7. OPTIONAL SAFETY LAYER (recommended) 
   Before final output: if weak_context_marker_present: suppress F2/F3 confidence 
   Examples: “in mice” “under conditions” “using method” 
   
8. OUTPUT 
Final system returns: { sentence, label: F1 | F2 | F3, confidence, supporting_anchor (optional) } 

9. DATASET STRATEGY (IMPORTANT SUMMARY) 
DistilBERT dataset: Broad Labels: CLEAN / F1 / F2 / UNCERTAIN 
SciBERT dataset: Strict Clean only Labels: F1 / F2 / F3 / NONE 

10. SYSTEM FLOW (COMPLETE) PDF ↓ Preprocessor (E-mode + Anchoring + Filtering) ↓ Windows ↓ DistilBERT (fast triage) ├── CLEAN → discard ├── F1/F2 (high confidence) → OUTPUT └── UNCERTAIN → SciBERT ↓ SciBERT classification ↓ Final filtering ↓ OUTPUT

11. WHAT THIS ARCHITECTURE OPTIMIZES 
✔ Efficiency Most data never hits SciBERT 
✔ Precision control High-confidence gating 
✔ Interpretability Anchors + epistemic structure preserved.

"""