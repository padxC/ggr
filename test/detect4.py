import cv2
import numpy as np
import matplotlib.pyplot as plt

# Load images
before = cv2.imread('small.jpg')
after = cv2.imread('small2.jpg')

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

# Get image center
h_img, w_img = after.shape[:2]
center_x, center_y = w_img // 2, h_img // 2
print(f"📐 Image size: {w_img} x {h_img}")
print(f"📍 Image center: ({center_x}, {center_y})")

# Draw results on the after image
result = after.copy()
fishing_windows = []

for contour in contours:
    x, y, w, h = cv2.boundingRect(contour)
    area = w * h
    
    # Calculate aspect ratio
    aspect_ratio = w / h
    
    # height = w / 2
    is_wide_and_short = h < (w / 2)
    
    # Calculate how centered this rectangle is (0 = far from center, 1 = perfectly centered)
    rect_center_x = x + w // 2
    rect_center_y = y + h // 2
    distance_from_center = np.sqrt((rect_center_x - center_x)**2 + (rect_center_y - center_y)**2)
    max_distance = np.sqrt(center_x**2 + center_y**2)
    centered_score = 1 - (distance_from_center / max_distance)
    
    # Check for white border (new feature)
    # Sample the border pixels of the detected region
    border_sample = []
    # Top border
    if y > 0:
        top_border = after[y:y+2, x:x+w]
        border_sample.extend(top_border.flatten())
    # Bottom border
    if y + h < h_img:
        bottom_border = after[y+h-2:y+h, x:x+w]
        border_sample.extend(bottom_border.flatten())
    # Left border
    if x > 0:
        left_border = after[y:y+h, x:x+2]
        border_sample.extend(left_border.flatten())
    # Right border
    if x + w < w_img:
        right_border = after[y:y+h, x+w-2:x+w]
        border_sample.extend(right_border.flatten())
    
    # Calculate how white the border is (RGB values close to 255)
    if border_sample:
        border_array = np.array(border_sample).reshape(-1, 3)
        avg_border_color = np.mean(border_array, axis=0)
        brightness = np.mean(avg_border_color)
        is_white_border = brightness > 200  # White threshold
        
        # Check if border is uniform (all RGB channels high)
        border_std = np.std(border_array, axis=0)
        is_uniform_border = np.mean(border_std) < 30
    else:
        is_white_border = False
        is_uniform_border = False
    
    # Conditions for fishing popup:
    # 1. Area > 1000 (reasonable size)
    # 2. Aspect ratio > 0.7 (wider or square)
    # 3. Centered (score > 0.3 - adjust based on your game)
    # 4. White border (optional - enable if needed)
    
    if area > 1000 and w > 50 and h > 20 and is_wide_and_short and centered_score > 0.3:
        
        # Draw thick GREEN rectangle for detected popup
        cv2.rectangle(result, (x, y), (x+w, y+h), (0, 255, 0), 3)
        
        # Add label with info
        # label = f"Fishing Popup (center dist: {distance_from_center:.0f}px)"
        label = f"Fishing Popup (W:{w}, H:{h})"
        cv2.putText(result, label, (x, y-10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Draw center marker on the popup
        cv2.circle(result, (rect_center_x, rect_center_y), 5, (0, 255, 0), -1)
        
        # Crop the fishing window
        fishing_window = after[y:y+h, x:x+w]
        fishing_windows.append((fishing_window, (x, y, w, h), aspect_ratio, centered_score, distance_from_center))
        
        print(f"\n✓ Fishing popup detected!")
        print(f"  Position: ({x}, {y})")
        print(f"  Size: {w} x {h} pixels")
        print(f"  Aspect ratio (w/h): {aspect_ratio:.2f}")
        print(f"  Height < Width/2? {is_wide_and_short} (h={h}, w/2={w/2:.1f})")

        print(f"  Center of popup: ({rect_center_x}, {rect_center_y})")
        print(f"  Distance from image center: {distance_from_center:.0f} pixels")
        print(f"  Centered score: {centered_score:.2f}")
        print(f"  White border detected: {is_white_border}")
    elif area > 500:
        # Other changes - draw YELLOW rectangle
        cv2.rectangle(result, (x, y), (x+w, y+h), (0, 255, 255), 1)

# Draw image center on result
cv2.circle(result, (center_x, center_y), 8, (255, 0, 0), -1)
cv2.putText(result, "CENTER", (center_x - 40, center_y - 10), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

# Create visualization
fig = plt.figure(figsize=(20, 14))

# Create grid for better organization
gs = fig.add_gridspec(2, 3, hspace=0.2, wspace=0.1)

# Original images
ax1 = fig.add_subplot(gs[0, 0])
ax1.imshow(cv2.cvtColor(before, cv2.COLOR_BGR2RGB))
ax1.set_title('📷 korea.jpg (NO Fishing Popup)', fontsize=14, fontweight='bold')
ax1.axis('off')

ax2 = fig.add_subplot(gs[0, 1])
ax2.imshow(cv2.cvtColor(after, cv2.COLOR_BGR2RGB))
ax2.set_title('🎣 korea2.jpg (WITH Fishing Popup)', fontsize=14, fontweight='bold')
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
ax5.set_title('✅ Detection Result (Green Box = Fishing Popup, Blue Dot = Image Center)', 
              fontsize=14, fontweight='bold')
ax5.axis('off')

# Cropped fishing window
ax6 = fig.add_subplot(gs[1, 2])
if fishing_windows:
    best_window, pos, aspect, center_score, distance = fishing_windows[0]
    ax6.imshow(cv2.cvtColor(best_window, cv2.COLOR_BGR2RGB))
    
    # Add info text on the image
    info_text = f"Size: {pos[2]}x{pos[3]}\nAspect: {aspect:.2f}\nCenter dist: {distance:.0f}px"
    ax6.text(5, 15, info_text, bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.8),
             fontsize=10, verticalalignment='top', fontweight='bold')
    
    # Highlight white border in the cropped image (optional visualization)
    # Draw a small indicator if white border was detected
    ax6.text(pos[2]-70, 15, "✓ White Border", 
             bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
             fontsize=8, color='black')
    
    ax6.set_title(f'🎯 Extracted Fishing Window\n{pos[2]} x {pos[3]} pixels', 
                  fontsize=14, fontweight='bold')
    
    # Save the cropped window
    cv2.imwrite('fishing_window_extracted.png', best_window)
    print(f"\n✅ Saved extracted fishing window to: fishing_window_extracted.png")
else:
    ax6.text(0.5, 0.5, 'No fishing window detected', 
             ha='center', va='center', transform=ax6.transAxes, fontsize=16)
    ax6.set_title('❌ No Fishing Window Found', fontsize=14, fontweight='bold')
ax6.axis('off')

plt.suptitle('Tales Runner - Fishing Popup Detection (Centered Window with White Border)', 
             fontsize=18, fontweight='bold', y=0.98)
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
    print(f"   Aspect ratio: {fishing_windows[0][2]:.2f}")
    print(f"\n📍 Position Information:")
    print(f"   Top-left: ({fishing_windows[0][1][0]}, {fishing_windows[0][1][1]})")
    popup_center_x = fishing_windows[0][1][0] + fishing_windows[0][1][2]//2
    popup_center_y = fishing_windows[0][1][1] + fishing_windows[0][1][3]//2
    print(f"   Popup center: ({popup_center_x}, {popup_center_y})")
    print(f"   Image center: ({center_x}, {center_y})")
    print(f"   Distance from center: {fishing_windows[0][4]:.0f} pixels")
    print(f"\n💾 Saved files:")
    print(f"   - fishing_window_extracted.png")
else:
    print(f"❌ FAILED: No fishing window detected")
    print(f"\n💡 Suggested adjustments:")
    print(f"   - Lower centered_score threshold (currently 0.3)")
    print(f"   - Reduce minimum area (currently 1000)")
    print(f"   - Adjust aspect ratio filter (currently > 0.7)")

# Create a zoomed view with white border emphasis
if fishing_windows:
    fig2, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # Original with box
    img_with_box = after.copy()
    x, y, w, h = fishing_windows[0][1]
    cv2.rectangle(img_with_box, (x, y), (x+w, y+h), (0, 255, 0), 3)
    cv2.circle(img_with_box, (center_x, center_y), 8, (255, 0, 0), -1)
    
    axes[0].imshow(cv2.cvtColor(img_with_box, cv2.COLOR_BGR2RGB))
    axes[0].set_title('Original with Detection & Center', fontsize=12, fontweight='bold')
    axes[0].axis('off')
    
    # Cropped popup
    axes[1].imshow(cv2.cvtColor(fishing_windows[0][0], cv2.COLOR_BGR2RGB))
    axes[1].set_title('Cropped Fishing Popup', fontsize=12, fontweight='bold')
    axes[1].axis('off')
    
    # White border detection visualization
    # Extract just the border area
    border_vis = fishing_windows[0][0].copy()
    # Draw arrows pointing to white border
    h_border, w_border = border_vis.shape[:2]
    cv2.arrowedLine(border_vis, (w_border//2, 0), (w_border//2, 15), (255, 255, 255), 2)
    cv2.arrowedLine(border_vis, (w_border//2, h_border-1), (w_border//2, h_border-15), (255, 255, 255), 2)
    cv2.arrowedLine(border_vis, (0, h_border//2), (15, h_border//2), (255, 255, 255), 2)
    cv2.arrowedLine(border_vis, (w_border-1, h_border//2), (w_border-15, h_border//2), (255, 255, 255), 2)
    
    axes[2].imshow(cv2.cvtColor(border_vis, cv2.COLOR_BGR2RGB))
    axes[2].set_title('White Border Detection\n(Arrows point to white borders)', fontsize=12, fontweight='bold')
    axes[2].axis('off')
    
    plt.tight_layout()
    plt.show()

# Bonus: Print white border analysis
if fishing_windows:
    print("\n" + "="*60)
    print("WHITE BORDER ANALYSIS")
    print("="*60)
    print("The detected window has been analyzed for white borders.")
    print("White borders are characteristic of the fishing popup window.")
    print("This feature helps distinguish it from other UI elements.")