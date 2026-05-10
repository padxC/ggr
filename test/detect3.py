import cv2
import numpy as np
import matplotlib.pyplot as plt

# Load images
before = cv2.imread('korea.jpg')
after = cv2.imread('korea2.jpg')

# Convert to grayscale
before_gray = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
after_gray = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)

# Calculate absolute difference
diff = cv2.absdiff(before_gray, after_gray)

# Apply Gaussian blur to reduce noise
diff_blur = cv2.GaussianBlur(diff, (5, 5), 0)

# Threshold to get changed areas
_, thresh = cv2.threshold(diff_blur, 25, 255, cv2.THRESH_BINARY)

# Morphological operations to clean up
kernel = np.ones((3, 3), np.uint8)
thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

# Find contours
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Draw results on the after image
result = after.copy()
fishing_windows = []

for contour in contours:
    x, y, w, h = cv2.boundingRect(contour)
    area = w * h
    
    # Filter by size and aspect ratio (wider than tall for fishing popup)
    aspect_ratio = w / h
    
    # Conditions for fishing popup:
    # 1. Area > 1000 (not too small)
    # 2. Aspect ratio between 0.8 and 1.5 (wider than tall or slightly square)
    # 3. Minimum dimensions
    if area > 1000 and w > 30 and h > 30 and aspect_ratio > 0.7:
        
        # For fishing popup specifically (wider than tall)
        if aspect_ratio >= 0.9:  # Width is equal or greater than height
            # Draw thicker green rectangle
            cv2.rectangle(result, (x, y), (x+w, y+h), (0, 255, 0), 3)
            
            # Add label
            cv2.putText(result, f"Fishing Popup", (x, y-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Crop the fishing window
            fishing_window = after[y:y+h, x:x+w]
            fishing_windows.append((fishing_window, (x, y, w, h), aspect_ratio))
            
            print(f"✓ Fishing popup detected!")
            print(f"  Position: ({x}, {y})")
            print(f"  Size: {w} x {h} pixels")
            print(f"  Aspect ratio (w/h): {aspect_ratio:.2f}")
        else:
            # Other changes (maybe noise) - draw red rectangle
            cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 1)
    elif area > 500:
        # Smaller changes - draw yellow rectangle
        cv2.rectangle(result, (x, y), (x+w, y+h), (0, 255, 255), 1)

# Create a larger visualization
fig = plt.figure(figsize=(20, 12))

# Create grid for better organization
gs = fig.add_gridspec(2, 3, hspace=0.2, wspace=0.1)

# Original images
ax1 = fig.add_subplot(gs[0, 0])
ax1.imshow(cv2.cvtColor(before, cv2.COLOR_BGR2RGB))
ax1.set_title('📷 kr.jpg (NO Fishing Popup)', fontsize=14, fontweight='bold')
ax1.axis('off')

ax2 = fig.add_subplot(gs[0, 1])
ax2.imshow(cv2.cvtColor(after, cv2.COLOR_BGR2RGB))
ax2.set_title('🎣 kr2.jpg (WITH Fishing Popup)', fontsize=14, fontweight='bold')
ax2.axis('off')

# Difference map
ax3 = fig.add_subplot(gs[0, 2])
diff_display = cv2.applyColorMap(diff, cv2.COLORMAP_JET)
ax3.imshow(cv2.cvtColor(diff_display, cv2.COLOR_BGR2RGB))
ax3.set_title('🔥 Difference Heatmap (Red/Yellow = Changes)', fontsize=14, fontweight='bold')
ax3.axis('off')

# Threshold mask
ax4 = fig.add_subplot(gs[1, 0])
ax4.imshow(thresh, cmap='gray')
ax4.set_title('⚪ Change Mask (White = Detected Changes)', fontsize=14, fontweight='bold')
ax4.axis('off')

# Detection result
ax5 = fig.add_subplot(gs[1, 1])
ax5.imshow(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
ax5.set_title('✅ Detection Result (Green Box = Fishing Popup)', fontsize=14, fontweight='bold')
ax5.axis('off')

# Cropped fishing window
ax6 = fig.add_subplot(gs[1, 2])
if fishing_windows:
    best_window, pos, aspect = fishing_windows[0]
    ax6.imshow(cv2.cvtColor(best_window, cv2.COLOR_BGR2RGB))
    
    # Add info text on the image
    info_text = f"Size: {pos[2]}x{pos[3]}\nAspect: {aspect:.2f}"
    ax6.text(5, 15, info_text, bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7),
             fontsize=10, verticalalignment='top')
    
    ax6.set_title(f'🎯 Extracted Fishing Window\n{pos[2]} x {pos[3]} pixels', fontsize=14, fontweight='bold')
    
    # Save the cropped window
    cv2.imwrite('fishing_window_extracted.png', best_window)
    print(f"\n✅ Saved extracted fishing window to: fishing_window_extracted.png")
else:
    ax6.text(0.5, 0.5, 'No fishing window detected', 
             ha='center', va='center', transform=ax6.transAxes, fontsize=16)
    ax6.set_title('❌ No Fishing Window Found', fontsize=14, fontweight='bold')
ax6.axis('off')

plt.suptitle('Tales Runner - Fishing Popup Detection', fontsize=18, fontweight='bold', y=0.98)
plt.tight_layout()
plt.show()

# Print detailed summary
print("\n" + "="*60)
print("DETECTION SUMMARY")
print("="*60)
if fishing_windows:
    print(f"✅ SUCCESS: Fishing popup detected!")
    print(f"\n📐 Popup Dimensions:")
    print(f"   Width:  {fishing_windows[0][1][2]} pixels")
    print(f"   Height: {fishing_windows[0][1][3]} pixels")
    print(f"   Aspect ratio: {fishing_windows[0][2]:.2f} (wider than tall: Yes)")
    print(f"\n📍 Position:")
    print(f"   X: {fishing_windows[0][1][0]}")
    print(f"   Y: {fishing_windows[0][1][1]}")
    print(f"\n💾 Saved files:")
    print(f"   - fishing_window_extracted.png")
    print(f"   - detection_visualization.png (screenshot this)")
else:
    print(f"❌ FAILED: No fishing window detected")
    print(f"\n💡 Try adjusting:")
    print(f"   - Threshold value (currently 25)")
    print(f"   - Minimum area (currently 1000 pixels)")
    print(f"   - Aspect ratio filter (currently > 0.7)")

# Optional: Create a zoomed view of just the popup
if fishing_windows:
    fig2, ax = plt.subplots(1, 2, figsize=(12, 6))
    
    # Original with box
    img_with_box = after.copy()
    x, y, w, h = fishing_windows[0][1]
    cv2.rectangle(img_with_box, (x, y), (x+w, y+h), (0, 255, 0), 3)
    
    ax[0].imshow(cv2.cvtColor(img_with_box, cv2.COLOR_BGR2RGB))
    ax[0].set_title('Original Image with Detection Box', fontsize=12, fontweight='bold')
    ax[0].axis('off')
    
    # Cropped popup (zoomed)
    ax[1].imshow(cv2.cvtColor(fishing_windows[0][0], cv2.COLOR_BGR2RGB))
    ax[1].set_title('Cropped Fishing Popup (Zoomed)', fontsize=12, fontweight='bold')
    ax[1].axis('off')
    
    plt.tight_layout()
    plt.show()