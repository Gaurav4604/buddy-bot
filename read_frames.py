import pyrealsense2 as rs
import numpy as np
import cv2

# Configure the pipeline for the T265 fisheye streams
pipeline = rs.pipeline()
config = rs.config()

# Enable both fisheye streams; channel 1 and channel 2 correspond to left and right cameras
config.enable_stream(rs.stream.fisheye, 1)
config.enable_stream(rs.stream.fisheye, 2)

# Start streaming
pipeline.start(config)

try:
    while True:
        # Wait for a coherent pair of frames: fisheye frames from both cameras
        frames = pipeline.wait_for_frames()
        left_frame = frames.get_fisheye_frame(1)
        right_frame = frames.get_fisheye_frame(2)

        # If frames are not available yet, skip iteration
        if not left_frame or not right_frame:
            continue

        # Convert images to numpy arrays
        left_image = np.asanyarray(left_frame.get_data())
        right_image = np.asanyarray(right_frame.get_data())

        # Combine both images side by side for display
        combined_image = np.hstack((left_image, right_image))
        cv2.imshow("T265 Fisheye Streams (Press q to exit)", combined_image)

        # Press 'q' to exit the display loop
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    # Stop the pipeline and close the window
    pipeline.stop()
    cv2.destroyAllWindows()
