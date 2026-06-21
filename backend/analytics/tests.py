from django.test import TestCase

# Create your tests here.
import matplotlib.pyplot as plt
import numpy as np
from sentence_transformers import SentenceTransformer

# 1. Provide exactly 9 topics/sentences to fill out our 3x3 grid
topics = [
    "NETWORK SECURITY: port 8080 exposed, 2 unpatched CVEs, SSL weak cipher.",
    "COMPLIANCE STATUS: SOC2 expired 217 days ago, ISO27001 missing.",
    "CONTRACT INFO: expires in 42 days, $2.4M spend, payment card data.",
    "BREACH HISTORY: confirmed breach August 2024, no client notification.",
    "OVERALL RISK: risk score 78 out of 100, under investigation no.",
    "IDENTITY ACCESS: MFA missing for 14% of admin accounts, stale API keys.",
    "DATA PROTECTION: backups unencrypted, production data used in staging.",
    "SUPPLY CHAIN: 4th-party hosting dependency lacks security validation.",
    "ENDPOINT SECURITY: EDR software absent on legacy Windows servers.",
]

# 2. Load the 768-dimension model
model = SentenceTransformer("all-mpnet-base-v2")
embeddings = model.encode(topics)  # Shape: (9, 768)

# 3. Shape each 768-dim vector into a 16x16 RGB patch (256 pixels total)
# No interpolation, no stretching—just direct restructuring.
patches = []
for emb in embeddings:
    # Scale from embedding distribution to byte space natively
    scaled = ((emb + 0.12) / 0.24) * 255
    clipped = np.clip(scaled, 0, 255).astype(np.uint8)

    # 768 numbers -> 256 pixels x 3 channels -> 16x16x3 patch
    patch_16x16 = clipped.reshape((16, 16, 3))
    patches.append(patch_16x16)

# 4. Construct the pure 3x3 master grid matrix (48x48 total image size)
# Row 1 (Top)
top_row = np.hstack([patches[0], patches[1], patches[2]])
# Row 2 (Middle)
mid_row = np.hstack([patches[3], patches[4], patches[5]])
# Row 3 (Bottom)
bot_row = np.hstack([patches[6], patches[7], patches[8]])

# Stack vertically to create the final unified image canvas
master_image = np.vstack([top_row, mid_row, bot_row])  # Shape: (48, 48, 3)

# 5. Render via Matplotlib
plt.figure(figsize=(6, 6))
plt.imshow(master_image, interpolation="nearest")

# Draw visual grid boundaries exactly on the 16 and 32-pixel marks
plt.axvline(15.5, color="white", linewidth=2, linestyle="--")
plt.axvline(31.5, color="white", linewidth=2, linestyle="--")
plt.axhline(15.5, color="white", linewidth=2, linestyle="--")
plt.axhline(31.5, color="white", linewidth=2, linestyle="--")

plt.title("Pure Semantic Grid (48x48 Total Image)", fontsize=12, pad=12)
plt.axis("off")
plt.tight_layout()
plt.show()

print(f"Master Image Canvas Shape: {master_image.shape}")
print("Individual Sub-Box Size: 16x16 pixels per topic")