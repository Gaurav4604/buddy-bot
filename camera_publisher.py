import pyrealsense2 as rs
import numpy as np
import cv2
import asyncio
import base64
import json
from buddy_bot_communication.client import Node


class CameraPublisher:
    def __init__(self, server_url):
        self.node = Node(server_url)

        # Configure the pipeline for the T265 fisheye streams
        self.pipeline = rs.pipeline()
        self.config = rs.config()

        # Enable both fisheye streams; channel 1 and channel 2 correspond to left and right cameras
        self.config.enable_stream(rs.stream.fisheye, 1)
        self.config.enable_stream(rs.stream.fisheye, 2)

        self.running = False

    async def connect(self):
        await self.node.connect()

    async def disconnect(self):
        await self.node.disconnect()

    def start_pipeline(self):
        self.pipeline.start(self.config)

    def stop_pipeline(self):
        self.pipeline.stop()

    async def publish_frames(self):
        self.running = True

        while self.running:
            try:
                # Wait for a coherent pair of frames: fisheye frames from both cameras
                frames = self.pipeline.wait_for_frames()
                left_frame = frames.get_fisheye_frame(1)
                right_frame = frames.get_fisheye_frame(2)

                # If frames are not available yet, skip iteration
                if not left_frame or not right_frame:
                    continue

                # Convert images to numpy arrays
                left_image = np.asanyarray(left_frame.get_data())
                right_image = np.asanyarray(right_frame.get_data())

                # Encode images as JPEG
                _, left_jpeg = cv2.imencode(
                    ".jpg", left_image, [cv2.IMWRITE_JPEG_QUALITY, 80]
                )
                _, right_jpeg = cv2.imencode(
                    ".jpg", right_image, [cv2.IMWRITE_JPEG_QUALITY, 80]
                )

                # Convert to base64 for transmission
                left_base64 = base64.b64encode(left_jpeg).decode("utf-8")
                right_base64 = base64.b64encode(right_jpeg).decode("utf-8")

                # Publish frames to respective channels
                await self.node.publish("/vision-channel-1", {"image": left_base64})
                await self.node.publish("/vision-channel-2", {"image": right_base64})

                # Add a small delay to control the frame rate
                await asyncio.sleep(0.03)  # ~30 FPS

            except Exception as e:
                print(f"Error publishing frames: {e}")
                await asyncio.sleep(1)  # Wait before retrying

    def stop(self):
        self.running = False
        self.stop_pipeline()


async def main():
    server_url = "http://172.22.7.122:7000"  # Replace with your server address
    camera_publisher = CameraPublisher(server_url)

    await camera_publisher.connect()
    camera_publisher.start_pipeline()

    try:
        print("Camera publisher started. Press Ctrl+C to exit.")
        await camera_publisher.publish_frames()
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        camera_publisher.stop()
        await camera_publisher.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
