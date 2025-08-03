import pyrealsense2 as rs
import numpy as np
import subprocess
import asyncio

class RealSenseRTSPStreamer:
    def __init__(self):
        # --- RealSense Pipeline Configuration (untouched) ---
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.fisheye, 1)  # Left
        self.config.enable_stream(rs.stream.fisheye, 2)  # Right

        # --- Stream and FFmpeg Configuration ---
        self.frame_width = 848
        self.frame_height = 800
        self.fps = 30
        self.ffmpeg_processes = []
        
        # Define the two RTSP push URLs for our local mediamtx server
        self.rtsp_urls = [
            'rtsp://localhost:8554/left',
            'rtsp://localhost:8554/right'
        ]

    def start_pipeline(self):
        print("Starting RealSense pipeline...")
        self.pipeline.start(self.config)
        print("✅ RealSense pipeline started.")

    def stop_pipeline(self):
        print("Stopping RealSense pipeline...")
        self.pipeline.stop()
        print("✅ RealSense pipeline stopped.")

    def start_streaming(self):
        print("🚀 Starting FFmpeg processes to push streams...")
        for url in self.rtsp_urls:
            # T265 Fisheye streams are 8-bit grayscale (Y8)
            # FFmpeg needs to know the input format is grayscale
            command = [
                'ffmpeg',
                '-f', 'rawvideo',
                '-pix_fmt', 'gray',  # Use 'gray' for 8-bit grayscale input
                '-s', f'{self.frame_width}x{self.frame_height}',
                '-r', str(self.fps),
                '-i', '-',  # Read from stdin
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-tune', 'zerolatency',
                '-pix_fmt', 'yuv420p', # Output format for compatibility
                '-f', 'rtsp',
                '-rtsp_transport', 'tcp',
                url
            ]
            # Launch one FFmpeg process per stream URL
            process = subprocess.Popen(command, stdin=subprocess.PIPE)
            self.ffmpeg_processes.append(process)
        print(f"✅ FFmpeg processes started for: {self.rtsp_urls}")

    async def publish_frames(self):
        print("Publishing frames... Press Ctrl+C to exit.")
        while True:
            try:
                # --- This RealSense capture block is unchanged ---
                frames = self.pipeline.wait_for_frames()
                left_frame = frames.get_fisheye_frame(1)
                right_frame = frames.get_fisheye_frame(2)

                if not left_frame or not right_frame:
                    continue

                left_image = np.asanyarray(left_frame.get_data())
                right_image = np.asanyarray(right_frame.get_data())
                # -----------------------------------------------

                # Write frames to the respective FFmpeg processes
                self.ffmpeg_processes[0].stdin.write(left_image.tobytes())
                self.ffmpeg_processes[1].stdin.write(right_image.tobytes())

                await asyncio.sleep(1 / self.fps)

            except BrokenPipeError:
                print("❌ FFmpeg process closed unexpectedly. Exiting.")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                break

    def stop(self):
        print("\nStopping all processes...")
        for process in self.ffmpeg_processes:
            if process.stdin:
                process.stdin.close()
            process.wait()
        self.stop_pipeline()
        print("✅ All processes stopped.")

async def main():
    streamer = RealSenseRTSPStreamer()
    streamer.start_pipeline()
    streamer.start_streaming()

    try:
        await streamer.publish_frames()
    except KeyboardInterrupt:
        pass
    finally:
        streamer.stop()

if __name__ == "__main__":
    asyncio.run(main())
