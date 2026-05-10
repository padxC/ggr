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

# Store all detections for analysis
all_detections = []

for contour in contours:
    x, y, w, h = cv2.boundingRect(contour)
    area = w * h
    
    if area < 500:
        continue
    
    # Calculate aspect ratio
    aspect_ratio = w / h
    
    # Check if height < width/2
    is_wide_and_short = h < (w / 2)
    
    # Calculate how centered this rectangle is
    rect_center_x = x + w // 2
    rect_center_y = y + h // 2
    distance_from_center = np.sqrt((rect_center_x - center_x)**2 + (rect_center_y - center_y)**2)
    max_distance = np.sqrt(center_x**2 + center_y**2)
    centered_score = 1 - (distance_from_center / max_distance)
    
    # Check for white border
    border_sample = []
    if y > 0:
        top_border = after[y:y+2, x:x+w]
        border_sample.extend(top_border.flatten())
    if y + h < h_img:
        bottom_border = after[y+h-2:y+h, x:x+w]
        border_sample.extend(bottom_border.flatten())
    if x > 0:
        left_border = after[y:y+h, x:x+2]
        border_sample.extend(left_border.flatten())
    if x + w < w_img:
        right_border = after[y:y+h, x+w-2:x+w]
        border_sample.extend(right_border.flatten())
    
    if border_sample:
        border_array = np.array(border_sample).reshape(-1, 3)
        avg_border_color = np.mean(border_array, axis=0)
        brightness = np.mean(avg_border_color)
        is_white_border = brightness > 180  # Lowered threshold
    else:
        is_white_border = False
        brightness = 0
    
    # Store detection for analysis
    detection_info = {
        'x': x, 'y': y, 'w': w, 'h': h,
        'area': area,
        'aspect_ratio': aspect_ratio,
        'is_wide_and_short': is_wide_and_short,
        'centered_score': centered_score,
        'distance': distance_from_center,
        'is_white_border': is_white_border,
        'border_brightness': brightness
    }
    all_detections.append(detection_info)
    
    # IMPROVED CONDITIONS for fishing popup:
    # Based on your data, detection 2 (285x120) is the real one
    # Real fishing window characteristics:
    # - Area should be large (34200 in your case)
    # - Width around 200-400 pixels
    # - Height around 100-200 pixels  
    # - Aspect ratio between 2.0 and 3.0
    # - Centered score > 0.4
    # - Border brightness > 100 (not pure white, but light)
    
    if (area > 10000 and           # Large area (real popup)
        w > 200 and w < 400 and    # Width in range
        h > 80 and h < 200 and     # Height in range
        aspect_ratio > 1.5 and aspect_ratio < 3.5 and  # Reasonable aspect ratio
        centered_score > 0.4 and   # Well centered
        is_wide_and_short):        # Wide and short
        
        # Draw thick GREEN rectangle for detected popup
        cv2.rectangle(result, (x, y), (x+w, y+h), (0, 255, 0), 3)
        
        # Add label with info
        label = f"Fishing Popup (W:{w}, H:{h})"
        cv2.putText(result, label, (x, y-10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Draw center marker on the popup
        cv2.circle(result, (rect_center_x, rect_center_y), 5, (0, 255, 0), -1)
        
        # Draw line to center
        cv2.line(result, (rect_center_x, rect_center_y), (center_x, center_y), (255, 100, 0), 2)
        
        # Crop the fishing window
        fishing_window = after[y:y+h, x:x+w]
        fishing_windows.append((fishing_window, (x, y, w, h), aspect_ratio, centered_score, distance_from_center))
        
        print(f"\n✓ Fishing popup detected!")
        print(f"  Position: ({x}, {y})")
        print(f"  Size: {w} x {h} pixels")
        print(f"  Aspect ratio (w/h): {aspect_ratio:.2f}")
        print(f"  Center score: {centered_score:.2f}")
        print(f"  Border brightness: {brightness:.0f}")
        
    elif area > 1000:
        # Other changes - draw color based on characteristics
        if is_wide_and_short and w > 200:
            # Wide bar - draw ORANGE (might be UI bar)
            cv2.rectangle(result, (x, y), (x+w, y+h), (0, 165, 255), 2)
            cv2.putText(result, f"Bar (W:{w}, H:{h})", (x, y-5), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 165, 255), 1)
        else:
            # Other noise - draw YELLOW
            cv2.rectangle(result, (x, y), (x+w, y+h), (0, 255, 255), 1)

# Draw image center on result with crosshair
cv2.circle(result, (center_x, center_y), 10, (255, 0, 0), 2)
cv2.circle(result, (center_x, center_y), 4, (255, 0, 0), -1)
cv2.line(result, (center_x - 20, center_y), (center_x - 10, center_y), (255, 0, 0), 2)
cv2.line(result, (center_x + 10, center_y), (center_x + 20, center_y), (255, 0, 0), 2)
cv2.line(result, (center_x, center_y - 20), (center_x, center_y - 10), (255, 0, 0), 2)
cv2.line(result, (center_x, center_y + 10), (center_x, center_y + 20), (255, 0, 0), 2)
cv2.putText(result, "CENTER", (center_x - 40, center_y - 15), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

# Create visualization
fig = plt.figure(figsize=(20, 14))
gs = fig.add_gridspec(2, 3, hspace=0.2, wspace=0.1)

# Original images
ax1 = fig.add_subplot(gs[0, 0])
ax1.imshow(cv2.cvtColor(before, cv2.COLOR_BGR2RGB))
ax1.set_title('📷 Before (NO Fishing Popup)', fontsize=14, fontweight='bold')
ax1.axis('off')

ax2 = fig.add_subplot(gs[0, 1])
ax2.imshow(cv2.cvtColor(after, cv2.COLOR_BGR2RGB))
ax2.set_title('🎣 After (WITH Fishing Popup)', fontsize=14, fontweight='bold')
ax2.axis('off')

# Difference map
ax3 = fig.add_subplot(gs[0, 2])
diff_display = cv2.applyColorMap(diff, cv2.COLORMAP_JET)
ax3.imshow(cv2.cvtColor(diff_display, cv2.COLOR_BGR2RGB))
ax3.set_title('🔥 Difference Heatmap', fontsize=14, fontweight='bold')
ax3.axis('off')

# Threshold mask
ax4 = fig.add_subplot(gs[1, 0])
ax4.imshow(thresh, cmap='gray')
ax4.set_title('⚪ Change Mask', fontsize=14, fontweight='bold')
ax4.axis('off')

# Detection result
ax5 = fig.add_subplot(gs[1, 1])
ax5.imshow(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
ax5.set_title('✅ Detection Result', fontsize=14, fontweight='bold')
ax5.axis('off')

# Cropped fishing window
ax6 = fig.add_subplot(gs[1, 2])
if fishing_windows:
    best_window, pos, aspect, center_score, distance = fishing_windows[0]
    ax6.imshow(cv2.cvtColor(best_window, cv2.COLOR_BGR2RGB))
    info_text = f"Size: {pos[2]}x{pos[3]}\nAspect: {aspect:.2f}"
    ax6.text(5, 15, info_text, bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.8),
             fontsize=10, verticalalignment='top', fontweight='bold')
    ax6.set_title(f'🎯 Extracted Fishing Window', fontsize=14, fontweight='bold')
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

# Print all detections for reference
print("\n" + "="*60)
print("ALL DETECTIONS ANALYZED")
print("="*60)
for i, det in enumerate(all_detections, 1):
    print(f"\nDetection {i}:")
    print(f"  Size: {det['w']} x {det['h']} (Area: {det['area']})")
    print(f"  Aspect ratio: {det['aspect_ratio']:.2f}")
    print(f"  Center score: {det['centered_score']:.3f}")
    print(f"  Border brightness: {det['border_brightness']:.0f}")
    print(f"  Wide & short: {det['is_wide_and_short']}")
    if det['w'] > 200 and det['h'] > 80 and det['area'] > 10000:
        print(f"  >>> THIS IS LIKELY THE FISHING WINDOW!")

# Print summary
print("\n" + "="*60)
print("DETECTION SUMMARY")
print("="*60)
if fishing_windows:
    print(f"✅ SUCCESS: Fishing popup detected correctly!")
    print(f"\n📐 Popup Dimensions: {fishing_windows[0][1][2]} x {fishing_windows[0][1][3]} pixels")
    print(f"📏 Aspect ratio: {fishing_windows[0][2]:.2f}")
    print(f"🎯 Center score: {fishing_windows[0][3]:.3f}")
else:
    print(f"❌ No fishing window detected with current thresholds")
    print(f"\n💡 Based on your data, the fishing window should be:")
    print(f"   - Size around 285 x 120 pixels")
    print(f"   - Area around 34200 pixels")
    print(f"   - Aspect ratio around 2.38")
    print(f"   - Center score around 0.55")