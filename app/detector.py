import cv2
import numpy as np

class Detector:

    @staticmethod
    def getWindow(beforeImage, afterImage):
        # Load images
        before = cv2.imread(beforeImage)
        after = cv2.imread(afterImage)

        # Convert to grayscale
        beforeGray = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
        afterGray = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)
        
        # Calculate absolute difference
        diff = cv2.absdiff(beforeGray, afterGray)
        
        # Apply Gaussian blur to reduce noise
        diffBlur = cv2.GaussianBlur(diff, (5, 5), 0)

        # Threshold to get changed areas
        _, thresh = cv2.threshold(diffBlur, 25, 255, cv2.THRESH_BINARY)

        # Morphological operations to clean up
        # dilates and erosion
        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Get image center
        h, w = after.shape[:2]
        center_x, center_y = w // 2, h // 2

        windows = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            
            aspectRatio = w / h
            
            rectCenter_x = x + w // 2
            rectCenter_y = y + h // 2
            distanceFromCenter = np.sqrt((rectCenter_x - center_x)**2 + (rectCenter_y - center_y)**2)
            maxDistance = np.sqrt(center_x**2 + center_y**2)
            centeredScore = 1 - (distanceFromCenter / maxDistance)
            
            if area > 1000 and h < (w / 2) and centeredScore > 0.3:
                window = after[y:y+h, x:x+w]
                windows.append((window, (x, y, w, h), aspectRatio, centeredScore, distanceFromCenter))
        
        return windows
    
    def getButton(image, low, high):
        """
        Detect button (Base on color)
        Returns: (x, y, w, h) position
        """
        # Convert to HSV color space
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Create mask for orange
        mask = cv2.inRange(hsv, low, high)
        
        # Clean up mask
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Find the largest orange region
        if contours:
            largest = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest)
            
            # Filter by minimum size
            if w > 30 and h > 15:
                return (x, y, w, h)
        
        return None



# Example usage
if __name__ == "__main__":
    result = Detector.getWindow('../test/kr.jpg', '../test/kr2.jpg')
    
    if result:
        print(f"\n✅ Found {len(result)} fishing window(s)")
        for i, (window, pos, ratio, score, distance) in enumerate(result):
            x, y, w, h = pos
            print(f"\n📊 Fishing Window {i+1}:")
            print(f"   Size: {w} x {h} pixels")
            print(f"   Position: ({x}, {y})")
            print(f"   Aspect Ratio: {ratio:.2f}")
            print(f"   Center Score: {score:.3f}")
            print(f"   Distance from center: {distance:.0f} pixels")
            
            # Save each detected window
            cv2.imwrite(f'fishing_window_{i+1}.png', window)
            print(f"   ✅ Saved: fishing_window_{i+1}.png")
    else:
        print("\n❌ No fishing window detected")