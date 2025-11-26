import sys
import os
import cv2
import time

# Add project root to path so we can import config if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

def capture_training_data():
    # Setup Paths
    output_dir = os.path.join("dataset", "raw_images")
    os.makedirs(output_dir, exist_ok=True)
    
    # Start Camera
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.REQUEST_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.REQUEST_HEIGHT)
    
    print(f"--- TRAINING DATA CAPTURE ---")
    print(f"Saving to: {output_dir}")
    print(f"Controls: [SPACE] to save image | [Q] to quit")
    
    count = 0
    # Check existing files to avoid overwriting
    existing_files = os.listdir(output_dir)
    count = len(existing_files)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
            
        # visual feedback
        display_frame = frame.copy()
        cv2.putText(display_frame, f"Saved: {count}", (50, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.rectangle(display_frame, (50, 50), (3840-50, 2160-50), (255, 0, 0), 2)
        
        # Resize for display on screen (since it's 4K)
        small_view = cv2.resize(display_frame, (1280, 720))
        cv2.imshow("Data Capture", small_view)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord(' '): # Spacebar
            filename = f"mtg_data_{count:04d}.jpg"
            filepath = os.path.join(output_dir, filename)
            cv2.imwrite(filepath, frame)
            print(f"Saved {filename}")
            count += 1
            # Flash screen effect
            cv2.imshow("Data Capture", np.zeros_like(small_view))
            cv2.waitKey(50)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    import numpy as np
    capture_training_data()