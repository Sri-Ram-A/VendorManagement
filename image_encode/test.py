import matplotlib.pyplot as plt
import numpy as np
from sentence_transformers import SentenceTransformer

# 1. Input Text - split cleanly line-by-line (5 lines total)
vendor_text = """NETWORK SECURITY: port 8080 exposed, 2 unpatched CVEs, SSL weak cipher.
COMPLIANCE STATUS: SOC2 expired 217 days ago, ISO27001 missing.
CONTRACT INFO: expires in 42 days, $2.4M spend, payment card data.
BREACH HISTORY: confirmed breach August 2024, no client notification.
OVERALL RISK: risk score 78 out of 100, under investigation no."""

lines = [line.strip() for line in vendor_text.strip().split("\n")]

# 2. Compute the embeddings (5 rows, each with 384 dimensions)
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(lines)  # Shape: (5, 384)

# 3. Interpolate each 384-dim vector to exactly 300 values (100 pixels * 3 channels)
# This completely bypasses the PCA sample-size restriction.
target_features = 300
resized_embeddings = np.zeros((len(lines), target_features))

for i in range(len(lines)):
    # Map the index range of 384 elements onto 300 elements smoothly
    resized_embeddings[i] = np.interp(
        np.linspace(0, 1, target_features),
        np.linspace(0, 1, 384),
        embeddings[i]
    )

# 4. Map values safely to the 0-255 byte bounds without distortion
scaled_data = ((resized_embeddings + 0.15) / 0.3) * 255
byte_data = np.clip(scaled_data, 0, 255).astype(np.uint8)

# 5. Reshape flat 300 values into 100-pixel long rows containing (R, G, B)
# Resulting Matrix Shape: (Height=5, Width=100, Channels=3)
image_matrix = byte_data.reshape((5, 100, 3))

# 6. Render the output via Matplotlib
plt.figure(figsize=(10, 3))
plt.imshow(image_matrix, interpolation="nearest", aspect="auto")

plt.title("Vendor Risk Matrix (100 Width x 5 Rows RGB)", fontsize=12, pad=10)
plt.ylabel("Text Lines")
plt.xlabel("Encoded Pixel Width (100 Columns)")
plt.yticks(ticks=range(5), labels=[f"Line {i}: {lines[i][:16]}..." for i in range(5)])
plt.tight_layout()
plt.show()

print(f"Constructed Image Matrix Shape: {image_matrix.shape}")