import cv2
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

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

# Store all detections for analysis
all_detections = []

print("="*80)
print("🔍 REVERSE ENGINEERING: Analyzing ALL detected regions")
print("="*80)

for contour in contours:
    x, y, w, h = cv2.boundingRect(contour)
    area = w * h
    
    if area < 500:  # Skip very small changes (noise)
        continue
    
    # Basic geometric features
    aspect_ratio = w / h
    is_wide_and_short = h < (w / 2)
    is_square = 0.8 < aspect_ratio < 1.2
    is_wide = aspect_ratio > 1.5
    is_tall = aspect_ratio < 0.7
    
    # Center features
    rect_center_x = x + w // 2
    rect_center_y = y + h // 2
    distance_from_center = np.sqrt((rect_center_x - center_x)**2 + (rect_center_y - center_y)**2)
    max_distance = np.sqrt(center_x**2 + center_y**2)
    centered_score = 1 - (distance_from_center / max_distance)
    
    # Border color analysis
    border_sample = []
    border_colors = []
    
    # Top border
    if y > 0:
        top_border = after[y:y+2, x:x+w]
        border_sample.extend(top_border.flatten())
        border_colors.append(('top', np.mean(top_border, axis=(0,1))))
    # Bottom border
    if y + h < h_img:
        bottom_border = after[y+h-2:y+h, x:x+w]
        border_sample.extend(bottom_border.flatten())
        border_colors.append(('bottom', np.mean(bottom_border, axis=(0,1))))
    # Left border
    if x > 0:
        left_border = after[y:y+h, x:x+2]
        border_sample.extend(left_border.flatten())
        border_colors.append(('left', np.mean(left_border, axis=(0,1))))
    # Right border
    if x + w < w_img:
        right_border = after[y:y+h, x+w-2:x+w]
        border_sample.extend(right_border.flatten())
        border_colors.append(('right', np.mean(right_border, axis=(0,1))))
    
    # Calculate border characteristics
    if border_sample:
        border_array = np.array(border_sample).reshape(-1, 3)
        avg_border_color = np.mean(border_array, axis=0)
        brightness = np.mean(avg_border_color)
        is_white_border = brightness > 200
        border_std = np.std(border_array, axis=0)
        is_uniform_border = np.mean(border_std) < 30
    else:
        is_white_border = False
        is_uniform_border = False
        avg_border_color = [0, 0, 0]
        brightness = 0
    
    # Interior analysis (what's inside the detected region)
    interior = after[y:y+h, x:x+w]
    interior_mean = np.mean(interior, axis=(0,1))
    interior_std = np.std(interior, axis=(0,1))
    interior_brightness = np.mean(interior_mean)
    
    # Edge density (how many edges inside the region)
    interior_gray = cv2.cvtColor(interior, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(interior_gray, 50, 150)
    edge_density = np.sum(edges > 0) / (w * h)
    
    # Texture complexity
    texture_complexity = np.std(interior_gray)
    
    # Store all features
    detection = {
        'bbox': (x, y, w, h),
        'area': area,
        'aspect_ratio': aspect_ratio,
        'is_wide_and_short': is_wide_and_short,
        'is_square': is_square,
        'is_wide': is_wide,
        'is_tall': is_tall,
        'centered_score': centered_score,
        'distance_from_center': distance_from_center,
        'is_white_border': is_white_border,
        'is_uniform_border': is_uniform_border,
        'border_brightness': brightness,
        'border_color': avg_border_color,
        'interior_mean': interior_mean,
        'interior_brightness': interior_brightness,
        'interior_std': interior_std,
        'edge_density': edge_density,
        'texture_complexity': texture_complexity,
        'contour': contour
    }
    
    all_detections.append(detection)

# Identify which one is likely the fishing window (by heuristics)
fishing_candidates = []
for det in all_detections:
    # Score each detection on fishing-window-likeness
    score = 0
    if det['is_wide_and_short']:
        score += 30
    if det['centered_score'] > 0.3:
        score += 25
    if det['is_white_border']:
        score += 20
    if det['area'] > 1000:
        score += 15
    if det['edge_density'] < 0.1:  # UI elements usually have clean edges
        score += 10
    
    det['fishing_score'] = score

# Sort by score
all_detections.sort(key=lambda x: x['fishing_score'], reverse=True)
fishing_window = all_detections[0] if all_detections else None

# Print detailed comparison
print("\n📊 FEATURE COMPARISON: Fishing Window vs Other Detections")
print("="*80)

if fishing_window:
    print(f"\n✅ FISHING WINDOW (Score: {fishing_window['fishing_score']}):")
    print(f"   📐 Size: {fishing_window['bbox'][2]} x {fishing_window['bbox'][3]} (Area: {fishing_window['area']})")
    print(f"   📏 Aspect ratio: {fishing_window['aspect_ratio']:.2f} (wide & short: {fishing_window['is_wide_and_short']})")
    print(f"   🎯 Center score: {fishing_window['centered_score']:.3f} (distance: {fishing_window['distance_from_center']:.0f}px)")
    print(f"   ⚪ White border: {fishing_window['is_white_border']} (brightness: {fishing_window['border_brightness']:.0f})")
    print(f"   🎨 Interior brightness: {fishing_window['interior_brightness']:.0f}")
    print(f"   🔲 Edge density: {fishing_window['edge_density']:.3f}")
    print(f"   📊 Texture complexity: {fishing_window['texture_complexity']:.1f}")

print("\n" + "-"*80)
print("📋 OTHER DETECTIONS (Noise/Other UI elements):")
print("-"*80)

for i, det in enumerate(all_detections[1:4], 1):  # Show top 3 other detections
    print(f"\n⚠️ Detection {i} (Score: {det['fishing_score']}):")
    print(f"   📐 Size: {det['bbox'][2]} x {det['bbox'][3]} (Area: {det['area']})")
    print(f"   📏 Aspect ratio: {det['aspect_ratio']:.2f} (wide & short: {det['is_wide_and_short']})")
    print(f"   🎯 Center score: {det['centered_score']:.3f}")
    print(f"   ⚪ White border: {det['is_white_border']} (brightness: {det['border_brightness']:.0f})")
    print(f"   🔲 Edge density: {det['edge_density']:.3f}")

# Find what makes the fishing window UNIQUE
print("\n" + "="*80)
print("🎯 KEY DIFFERENCES (What makes the fishing window unique)")
print("="*80)

if fishing_window:
    features = []
    for det in all_detections[1:]:  # Compare with others
        # Compare aspect ratio
        if fishing_window['is_wide_and_short'] and not det['is_wide_and_short']:
            features.append("✓ WIDE & SHORT shape (height < width/2) - UNIQUE to fishing window")
        
        # Compare white border
        if fishing_window['is_white_border'] and not det['is_white_border']:
            features.append("✓ WHITE BORDER - Fishing window has bright white borders")
        
        # Compare center score
        if fishing_window['centered_score'] > det['centered_score'] + 0.2:
            features.append("✓ CENTERED POSITION - Fishing window is much closer to screen center")
        
        # Compare area
        if fishing_window['area'] > 2000 and det['area'] < 1000:
            features.append("✓ LARGER SIZE - Fishing window is significantly bigger")
        
        # Compare edge density
        if fishing_window['edge_density'] < 0.05 and det['edge_density'] > 0.1:
            features.append("✓ CLEAN EDGES - Fishing window has smooth UI edges (low edge density)")
        
        # Compare texture
        if fishing_window['texture_complexity'] < 50 and det['texture_complexity'] > 60:
            features.append("✓ UNIFORM TEXTURE - Fishing window has consistent UI texture")

# Remove duplicates
features = list(dict.fromkeys(features))

if features:
    for f in features[:10]:  # Show top 10
        print(f)
else:
    print("Analyzing differences...")

# Create visualization showing all detected regions with their scores
result_viz = after.copy()

# Color mapping for scores
for det in all_detections:
    x, y, w, h = det['bbox']
    score = det['fishing_score']
    
    # Color based on score (green = high = likely fishing window)
    if score > 50:
        color = (0, 255, 0)  # Green - Fishing window
        thickness = 3
    elif score > 30:
        color = (0, 255, 255)  # Yellow - Possible
        thickness = 2
    else:
        color = (0, 0, 255)  # Red - Low chance
        thickness = 1
    
    cv2.rectangle(result_viz, (x, y), (x+w, y+h), color, thickness)
    
    # Add score label
    label = f"Score:{score}"
    cv2.putText(result_viz, label, (x, y-5), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    
    # Add feature icons
    if det['is_wide_and_short']:
        cv2.putText(result_viz, "WIDE", (x+2, y+15), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255,255,0), 1)
    if det['is_white_border']:
        cv2.putText(result_viz, "WHITE", (x+2, y+25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255,255,255), 1)

# Draw center
cv2.circle(result_viz, (center_x, center_y), 8, (255, 0, 0), -1)

# Create summary visualization
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Original with all detections
axes[0,0].imshow(cv2.cvtColor(result_viz, cv2.COLOR_BGR2RGB))
axes[0,0].set_title('All Detections (Green=Fishing Window, Yellow=Possible, Red=Noise)', fontsize=12)
axes[0,0].axis('off')

# Feature comparison bar chart
if fishing_window:
    features_to_plot = ['Wide&Short', 'White Border', 'Centered', 'Clean Edges']
    fishing_values = [
        1 if fishing_window['is_wide_and_short'] else 0,
        1 if fishing_window['is_white_border'] else 0,
        fishing_window['centered_score'],
        1 if fishing_window['edge_density'] < 0.05 else 0
    ]
    
    # Average of other detections
    other_values = []
    for feature in ['is_wide_and_short', 'is_white_border', 'centered_score', 'edge_density']:
        if feature == 'edge_density':
            vals = [1 if d['edge_density'] < 0.05 else 0 for d in all_detections[1:3]] if len(all_detections) > 1 else [0]
        elif feature == 'centered_score':
            vals = [d['centered_score'] for d in all_detections[1:3]] if len(all_detections) > 1 else [0]
        else:
            vals = [1 if d[feature] else 0 for d in all_detections[1:3]] if len(all_detections) > 1 else [0]
        other_values.append(np.mean(vals) if vals else 0)
    
    x = np.arange(len(features_to_plot))
    width = 0.35
    
    axes[0,1].bar(x - width/2, fishing_values, width, label='Fishing Window', color='green', alpha=0.7)
    axes[0,1].bar(x + width/2, other_values, width, label='Other Detections', color='red', alpha=0.7)
    axes[0,1].set_ylabel('Score (0-1)')
    axes[0,1].set_title('Feature Comparison: Fishing Window vs Others')
    axes[0,1].set_xticks(x)
    axes[0,1].set_xticklabels(features_to_plot)
    axes[0,1].legend()
    axes[0,1].set_ylim(0, 1.2)

# Size comparison
if len(all_detections) > 1:
    areas = [d['area'] for d in all_detections[:5]]
    labels = [f"Detect {i+1}" for i in range(min(5, len(all_detections)))]
    labels[0] = "Fishing Window"
    
    colors = ['green'] + ['orange'] * (len(labels)-1)
    axes[1,0].bar(labels, areas, color=colors, alpha=0.7)
    axes[1,0].set_ylabel('Area (pixels)')
    axes[1,0].set_title('Size Comparison')
    axes[1,0].tick_params(axis='x', rotation=45)

# Feature importance chart
feature_importance = {
    'Wide & Short\n(h < w/2)': 30,
    'White Border': 25,
    'Centered\n(score > 0.3)': 20,
    'Clean Edges': 15,
    'Size > 1000px': 10
}

axes[1,1].barh(list(feature_importance.keys()), list(feature_importance.values()), color='blue', alpha=0.6)
axes[1,1].set_xlabel('Importance Score')
axes[1,1].set_title('Feature Importance for Detection')
axes[1,1].set_xlim(0, 35)

plt.tight_layout()
plt.show()

# Print recommendation
print("\n" + "="*80)
print("💡 RECOMMENDATIONS FOR HIGHER ACCURACY")
print("="*80)
print("""
Based on the analysis, use these thresholds for optimal detection:

1. PRIMARY FILTER (Most important):
   - Height < Width/2  (is_wide_and_short = True)
   
2. SECONDARY FILTER (Highly recommended):
   - White border brightness > 200
   - Centered score > 0.3
   
3. TERTIARY FILTER (For fine-tuning):
   - Area between 1000-50000 pixels
   - Edge density < 0.1 (clean UI edges)
   
OPTIMAL DETECTION CONDITION:
   if (area > 1000 and 
       w > 50 and 
       h > 20 and 
       h < (w / 2) and 
       centered_score > 0.3 and 
       is_white_border):
       # This is your fishing window!
""")

# Save analysis results
print(f"\n📊 Analysis complete!")
print(f"   Total detections found: {len(all_detections)}")
print(f"   Fishing window score: {fishing_window['fishing_score'] if fishing_window else 0}")