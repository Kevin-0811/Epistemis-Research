"""
0. Problem Definition (lock this in)
Input  : single sentence (no context) + optional [ANCHOR]/[NO_ANCHOR]
Output : 4-way label → {CLEAN, F1, F2, UNCERTAIN}
Goal   :
  - High precision on CLEAN/F1/F2
  - High recall on UNCERTAIN
1. Dataset Schema (FINAL)

Each sample MUST look like:

{
  "id": "F2_0123",
  "sentence": "[NO_ANCHOR] Dopamine influences reward learning.",
  "label": "F2",
  "tier": "T1"
}
Hard constraints
✔ No prev / next
✔ No source
✔ Sentence must be self-contained
✔ Edge-case CLEAN removed
✔ Anchor token prepended
2. Label Encoding
label2id = {
    "CLEAN": 0,
    "F1": 1,
    "F2": 2,
    "UNCERTAIN": 3
}

id2label = {v: k for k, v in label2id.items()}
3. Train / Validation Split

Do NOT random split blindly.

Stratified split:
Train: 80%
Val  : 20%

Maintain distribution:
- labels
- tiers
Why:
You want validation to reflect real difficulty, not randomness
4. Tokenization (critical details)
Model:
from transformers import DistilBertTokenizerFast

tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
Encoding:
def tokenize(example):
    return tokenizer(
        example["sentence"],
        truncation=True,
        padding="max_length",
        max_length=128
    )
Why 128?
Your sentences are short → anything >128 is wasted compute
5. Dataset Object (HuggingFace)
from datasets import load_dataset

dataset = load_dataset("json", data_files={
    "train": "train.jsonl",
    "validation": "val.jsonl"
})
Apply tokenization:
dataset = dataset.map(tokenize, batched=True)
Format:
dataset = dataset.rename_column("label", "labels")
dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])
6. Model Setup
from transformers import DistilBertForSequenceClassification

model = DistilBertForSequenceClassification.from_pretrained(
    "distilbert-base-uncased",
    num_labels=4,
    id2label=id2label,
    label2id=label2id
)
7. LOSS DESIGN (this is where most people fail)

You are NOT symmetric.

Class weights (IMPORTANT)
import torch

class_weights = torch.tensor([1.0, 1.2, 1.2, 2.5])

Meaning:

CLEAN      → 1.0
F1, F2     → 1.2
UNCERTAIN  → 2.5  ← CRITICAL
Custom loss:
from torch.nn import CrossEntropyLoss

loss_fn = CrossEntropyLoss(weight=class_weights)
Inject into Trainer via subclass
from transformers import Trainer

class WeightedTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")

        loss = loss_fn(logits, labels)

        return (loss, outputs) if return_outputs else loss
8. Training Arguments
from transformers import TrainingArguments

training_args = TrainingArguments(
    output_dir="./results",

    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,

    num_train_epochs=4,

    evaluation_strategy="epoch",
    save_strategy="epoch",

    logging_dir="./logs",

    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",

    weight_decay=0.01
)
9. Metrics (DO NOT USE ACCURACY ONLY)
Define:
from sklearn.metrics import precision_score, recall_score, f1_score
import numpy as np

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=1)

    return {
        "precision_macro": precision_score(labels, preds, average="macro"),
        "recall_macro": recall_score(labels, preds, average="macro"),
        "f1_macro": f1_score(labels, preds, average="macro"),

        # critical metric
        "uncertain_recall": recall_score(
            labels, preds,
            labels=[3], average=None
        )[0]
    }
What you actually watch:
PRIMARY   → uncertain_recall
SECONDARY → precision_macro
IGNORE    → accuracy (mostly useless here)
10. Training
trainer = WeightedTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["validation"],
    tokenizer=tokenizer,
    compute_metrics=compute_metrics
)

trainer.train()
11. Evaluation (post-training)
Confusion Matrix (MANDATORY)
from sklearn.metrics import confusion_matrix

cm = confusion_matrix(labels, preds)
What you check:
UNCERTAIN → CLEAN  ← must be minimal
CLEAN → UNCERTAIN  ← acceptable
12. Threshold Layer (for later routing)

Even though training is 4-way:

You will later compute:

probs = softmax(logits)

p_uncertain = probs[:, 3]

Then routing:

if p_uncertain > 0.3:
    route = "ESCALATE"
else:
    route = "PASS"
13. Tier Handling (IMPORTANT)

You already built tiers.

Use them:

During training:

Add sample weights:

Tier1 → weight 1.0
Tier2 → weight 1.5
Tier3 → weight 2.5 (later)

This requires extending dataset with sample_weight.

14. Sanity Checks (before training)

Run these or regret it:

✔ Check label distribution
from collections import Counter
print(Counter(dataset["train"]["labels"]))
✔ Check token length
max(len(x) for x in dataset["train"]["input_ids"])
✔ Check anchor presence
sum("[ANCHOR]" in s for s in raw_sentences)
15. Failure modes to watch
🔴 If UNCERTAIN recall < 0.75

→ increase class weight

🔴 If everything becomes UNCERTAIN

→ reduce weight or fix dataset

🔴 If CLEAN precision drops

→ check edge-case filtering again

16. Iteration (Tier 3 integration)

After training:

Collect:
UNCERTAIN misclassified as CLEAN

→ validate → add to Tier 3 → retrain

Final Structure (clean view)
Dataset → Clean → Tokenize → Weighted Training → Evaluate → Iterate
"""