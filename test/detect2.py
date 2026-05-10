import cv2
import numpy as np
import matplotlib.pyplot as plt

# Load images
before = cv2.imread('kr.jpg')
after = cv2.imread('kr2.jpg')

# Convert to grayscale
before_gray = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
after_gray = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)

# Calculate absolute difference
diff = cv2.absdiff(before_gray, after_gray)

# Threshold to get changed areas
_, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

# Find contours
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Draw results on the after image
result = after.copy()

for contour in contours:
    x, y, w, h = cv2.boundingRect(contour)
    if w * h > 500:  # Filter small noise
        cv2.rectangle(result, (x, y), (x+w, y+h), (0, 255, 0), 2)

# Display
fig, axes = plt.subplots(1, 4, figsize=(16, 5))

axes[0].imshow(cv2.cvtColor(before, cv2.COLOR_BGR2RGB))
axes[0].set_title('kr.jpg (No Popup)')
axes[0].axis('off')

axes[1].imshow(cv2.cvtColor(after, cv2.COLOR_BGR2RGB))
axes[1].set_title('kr2.jpg (With Popup)')
axes[1].axis('off')

axes[2].imshow(diff, cmap='gray')
axes[2].set_title('Difference Map')
axes[2].axis('off')

axes[3].imshow(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
axes[3].set_title('Detected Changes (Green Boxes)')
axes[3].axis('off')

plt.tight_layout()
plt.show()