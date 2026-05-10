import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import matplotlib.pyplot as plt

# Load your images
before_img = cv2.imread('kr.jpg')      # No popup
after_img = cv2.imread('kr2.jpg')      # Has popup

# Convert to RGB for matplotlib display
before_rgb = cv2.cvtColor(before_img, cv2.COLOR_BGR2RGB)
after_rgb = cv2.cvtColor(after_img, cv2.COLOR_BGR2RGB)

# Convert to grayscale for processing
before_gray = cv2.cvtColor(before_img, cv2.COLOR_BGR2GRAY)
after_gray = cv2.cvtColor(after_img, cv2.COLOR_BGR2GRAY)

# Method 1: SSIM (Structural Similarity)
score, diff = ssim(before_gray, after_gray, full=True)
diff = (diff * 255).astype("uint8")

# Threshold the difference
thresh = cv2.threshold(diff, 0.8 * 255, 255, cv2.THRESH_BINARY_INV)[1]

# Find contours of changed regions
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Create a copy to draw on
result_img = after_rgb.copy()

fishing_windows = []
for i, contour in enumerate(sorted(contours, key=cv2.contourArea, reverse=True)):
    x, y, w, h = cv2.boundingRect(contour)
    area = w * h
    
    # Filter by size (adjust these values based on your images)
    if area > 1000:  # Minimum area to consider
        # Draw rectangle on result image
        cv2.rectangle(result_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(result_img, f"Region {i+1}", (x, y-5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Crop the fishing window
        fishing_window = after_rgb[y:y+h, x:x+w]
        fishing_windows.append((fishing_window, (x, y, w, h)))
        
        print(f"Region {i+1}: Position=({x},{y}), Size={w}x{h}, Area={area}")

# Create visualization
fig, axes = plt.subplots(2, 3, figsize=(18, 12))

# Row 1: Original images
axes[0, 0].imshow(before_rgb)
axes[0, 0].set_title('Image 1: kr.jpg (No Fishing Window)', fontsize=12)
axes[0, 0].axis('off')

axes[0, 1].imshow(after_rgb)
axes[0, 1].set_title('Image 2: kr2.jpg (Has Fishing Window)', fontsize=12)
axes[0, 1].axis('off')

# Row 1 col 3: Difference map
axes[0, 2].imshow(diff, cmap='hot')
axes[0, 2].set_title('Difference Map (Hotter = More Change)', fontsize=12)
axes[0, 2].axis('off')

# Row 2: Detection results
axes[1, 0].imshow(thresh, cmap='gray')
axes[1, 0].set_title('Thresholded Differences (White = Changed)', fontsize=12)
axes[1, 0].axis('off')

axes[1, 1].imshow(result_img)
axes[1, 1].set_title('Detected Regions (Green Boxes)', fontsize=12)
axes[1, 1].axis('off')

# Show the cropped fishing window if found
if fishing_windows:
    best_window, pos = fishing_windows[0]  # Largest region
    axes[1, 2].imshow(best_window)
    axes[1, 2].set_title(f'Cropped Fishing Window\n{pos[2]}x{pos[3]} pixels', fontsize=12)
    axes[1, 2].axis('off')
    
    # Save the cropped fishing window
    cv2.imwrite('fishing_window_cropped.png', cv2.cvtColor(best_window, cv2.COLOR_RGB2BGR))
    print(f"\n✅ Saved fishing window to: fishing_window_cropped.png")
else:
    axes[1, 2].text(0.5, 0.5, 'No fishing window detected', 
                    ha='center', va='center', transform=axes[1, 2].transAxes)
    axes[1, 2].set_title('Cropped Fishing Window', fontsize=12)
    axes[1, 2].axis('off')
    print("\n❌ No fishing window detected")

plt.tight_layout()
plt.savefig('detection_visualization.png', dpi=150, bbox_inches='tight')
plt.show()

# Print summary
print("\n" + "="*50)
print("SUMMARY")
print("="*50)
print(f"SSIM Score: {score:.4f} (1.0 = identical, lower = more different)")
print(f"Number of changed regions found: {len(fishing_windows)}")
if fishing_windows:
    print(f"Largest region size: {fishing_windows[0][1][2]} x {fishing_windows[0][1][3]}")
    print(f"Position: ({fishing_windows[0][1][0]}, {fishing_windows[0][1][1]})")