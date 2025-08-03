import asyncio
import json
import cv2  # Import OpenCV
import numpy as np  # Import numpy for image data
from typing import Dict, List, Any, Set, Optional, Callable, Tuple
import concurrent.futures  # Import for ThreadPoolExecutor
import threading  # Import for managing display loop in a separate thread
import functools  # Import functools for partial

# Import pyrealsense2
import pyrealsense2 as rs

# Assuming the Node class is in a file named rtc_client_node.py
# from rtc_client_node import Node, CHANNEL_TYPE_CHAT, CHANNEL_TYPE_VIDEO_FORMAT

# For demonstration purposes, we'll include the Node class definition here
# In a real application, you would import it from the separate file.

import aiohttp
from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    RTCIceCandidate,
    RTCDataChannel,
)
from aiortc.rtcconfiguration import RTCConfiguration, RTCIceServer

# Constants for data channel types (repeated for clarity in this standalone sample)
CHANNEL_TYPE_CHAT = "chat"
CHANNEL_TYPE_VIDEO_FORMAT = "video-stream-{}"


class Node:
    def __init__(
        self,
        peer_id: int,
        signaling_url: str = "ws://localhost:8080/ws",
        num_video_streams: int = 0,  # Number of video streams this node will handle (send/receive)
    ) -> None:
        self.peer_id = peer_id
        self.signaling_url = signaling_url
        self.num_video_streams = num_video_streams

        self._pcs: Dict[int, RTCPeerConnection] = {}

        # Data channels for chat (keyed by target_id)
        self._chat_outgoing_channels: Dict[int, RTCDataChannel] = {}
        self._chat_incoming_channels: Dict[int, RTCDataChannel] = {}

        # Data channels for video (keyed by target_id, then by stream_index)
        self._video_outgoing_channels: Dict[int, Dict[int, RTCDataChannel]] = {}
        self._video_incoming_channels: Dict[int, Dict[int, RTCDataChannel]] = {}

        self._running = True
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None

        # Public handlers for incoming messages - can be overridden or assigned
        self.on_chat_message_received: Callable[[int, str], None] = (
            self._default_chat_handler
        )
        # Video handler now receives stream_index as well
        self.on_video_stream_data_received: Callable[[int, int, bytes], None] = (
            self._default_video_handler
        )

    async def _create_peer_connection(self, other_id: int) -> RTCPeerConnection:
        """Create and configure a new RTCPeerConnection for communication with other_id."""
        config = RTCConfiguration([RTCIceServer(urls="stun:stun.l.google.com:19302")])
        pc = RTCPeerConnection(configuration=config)
        self._pcs[other_id] = pc

        # Initialize channel dictionaries for this peer
        self._video_outgoing_channels[other_id] = {}
        self._video_incoming_channels[other_id] = {}

        # Create a data channel for chat
        chat_channel = pc.createDataChannel(CHANNEL_TYPE_CHAT)
        self._chat_outgoing_channels[other_id] = chat_channel

        @chat_channel.on("open")
        def on_chat_open() -> None:
            print(f"[{self.peer_id}] Outgoing Chat DataChannel to {other_id} opened")

        @chat_channel.on("message")
        def on_chat_message(message: str) -> None:
            self.on_chat_message_received(other_id, message)

        # Create data channels for each video stream this node handles
        for stream_index in range(self.num_video_streams):
            channel_label = CHANNEL_TYPE_VIDEO_FORMAT.format(stream_index)
            video_channel = pc.createDataChannel(channel_label)
            self._video_outgoing_channels[other_id][stream_index] = video_channel

            # Message handler for outgoing video channels (usually not used for receiving)
            @video_channel.on("message")
            def on_video_message(message: bytes) -> None:
                pass

        # Handle INCOMING data channels created by the remote peer
        @pc.on("datachannel")
        def on_datachannel(incoming_channel: RTCDataChannel) -> None:
            channel_label = incoming_channel.label
            print(
                f"[{self.peer_id}] Incoming DataChannel '{channel_label}' from {other_id} received"
            )

            if channel_label == CHANNEL_TYPE_CHAT:
                self._chat_incoming_channels[other_id] = incoming_channel

                @incoming_channel.on("open")
                def _chat_open() -> None:
                    print(
                        f"[{self.peer_id}] Incoming Chat DataChannel from {other_id} opened"
                    )

                @incoming_channel.on("message")
                def _chat_msg(m: str) -> None:
                    self.on_chat_message_received(other_id, m)

            elif channel_label.startswith("video-stream-"):
                try:
                    stream_index = int(channel_label.split("-")[-1])
                    if (
                        stream_index < self.num_video_streams
                    ):  # Only handle if we expect this stream index
                        self._video_incoming_channels[other_id][
                            stream_index
                        ] = incoming_channel

                        @incoming_channel.on("open")
                        def _video_open() -> None:
                            print(
                                f"[{self.peer_id}] Incoming Video DataChannel '{channel_label}' from {other_id} opened"
                            )

                        # Use partial to pass stream_index to the message handler
                        on_video_msg_partial = functools.partial(
                            self.on_video_stream_data_received, other_id, stream_index
                        )
                        incoming_channel.on("message")(on_video_msg_partial)
                    else:
                        print(
                            f"[{self.peer_id}] Received video channel with unexpected stream index: {channel_label}"
                        )

                except (ValueError, IndexError):
                    print(
                        f"[{self.peer_id}] Received video channel with invalid label format: {channel_label}"
                    )

            else:
                print(
                    f"[{self.peer_id}] Received unknown data channel type: {channel_label}"
                )

        @pc.on("icecandidate")
        async def on_icecandidate(event: Any) -> None:
            if event.candidate and self._ws and not self._ws.closed:
                candidate_data = {
                    "candidate": event.candidate.sdp,
                    "sdpMid": event.candidate.sdp_mid,
                    "sdpMLineIndex": event.candidate.sdp_m_line_index,
                }
                try:
                    await self._ws.send_json(
                        {
                            "from": self.peer_id,
                            "to": other_id,
                            "type": "candidate",
                            "data": candidate_data,
                        }
                    )
                except Exception:
                    pass

        @pc.on("connectionstatechange")
        async def on_connectionstatechange() -> None:
            print(
                f"[{self.peer_id}] Connection state with {other_id}: {pc.connectionState}"
            )
            if pc.connectionState == "failed":
                print(
                    f"[{self.peer_id}] Connection with {other_id} failed. Attempting ICE restart."
                )
                try:
                    await pc.restartIce()
                    if self.peer_id < other_id and self._ws and not self._ws.closed:
                        print(
                            f"[{self.peer_id}] Re-sending offer to {other_id} after ICE restart."
                        )
                        offer = await pc.createOffer()
                        await pc.setLocalDescription(offer)
                        await self._ws.send_json(
                            {
                                "from": self.peer_id,
                                "to": other_id,
                                "type": "offer",
                                "data": {
                                    "sdp": pc.localDescription.sdp,
                                    "type": pc.localDescription.type,
                                },
                            }
                        )

                except Exception as e:
                    print(
                        f"[{self.peer_id}] Error during ICE restart with {other_id}: {e}"
                    )
            elif pc.connectionstate == "closed":
                print(f"[{self.peer_id}] PeerConnection with {other_id} closed.")
                # Clean up local references when PC closes
                if other_id in self._pcs:
                    del self._pcs[other_id]
                if other_id in self._chat_outgoing_channels:
                    del self._chat_outgoing_channels[other_id]
                if other_id in self._chat_incoming_channels:
                    del self._chat_incoming_channels[other_id]
                if other_id in self._video_outgoing_channels:
                    del self._video_outgoing_channels[other_id]
                if other_id in self._video_incoming_channels:
                    del self._video_incoming_channels[other_id]

        return pc

    async def send_chat_message(self, message: str) -> None:
        """Sends a text message to all open chat data channels."""
        if not message.strip():
            return

        sent_count = 0
        for target_id, channel in list(self._chat_outgoing_channels.items()):
            if channel.readyState == "open":
                try:
                    channel.send(message)
                    sent_count += 1
                except Exception:
                    pass  # Suppress frequent errors

        if sent_count == 0 and self._chat_outgoing_channels:
            print(f"[{self.peer_id}] No open chat data channels to send message.")

    async def send_video_frame(self, stream_index: int, frame_data: bytes) -> None:
        """Sends a video frame's raw bytes for a specific stream to all open video channels."""
        if stream_index < 0 or stream_index >= self.num_video_streams:
            # This should ideally not happen if external logic is correct
            # print(f"[{self.peer_id}] Warning: Attempted to send video frame for out-of-bounds stream index {stream_index}.")
            return

        # Send this frame data over the specific outgoing channel for this stream
        # to all connected peers that have that channel open.
        sent_count = 0
        for target_id, channels_by_stream in list(
            self._video_outgoing_channels.items()
        ):
            if stream_index in channels_by_stream:
                channel = channels_by_stream[stream_index]
                if channel.readyState == "open":
                    try:
                        # Data channels have a send buffer. If it's full, send() might block
                        # or raise an error depending on implementation/settings.
                        channel.send(frame_data)
                        sent_count += 1
                    except Exception:
                        pass  # Suppress frequent errors

        # print(f"[{self.peer_id}] Sent video frame for stream {stream_index} to {sent_count} peers.") # Too chatty

    # --- Default Handlers for Incoming Messages ---
    def _default_chat_handler(self, peer_id: int, message: str) -> None:
        """Default handler for received chat messages."""
        print(f"[{self.peer_id}] Received chat from {peer_id}: {message}")

    def _default_video_handler(
        self, peer_id: int, stream_index: int, frame_data: bytes
    ) -> None:
        """
        Default handler for received video stream data.
        Does nothing by default. External logic should assign a handler.
        """
        pass

    async def connect_to(self, peer_ids: List[int]) -> None:
        """Connect this node to specified peer_ids via signaling and WebRTC."""
        async with aiohttp.ClientSession() as session:
            self._ws = None
            try:
                self._ws = await session.ws_connect(self.signaling_url)
                print(f"[{self.peer_id}] Registered with signaling server")

                await self._ws.send_json(
                    {
                        "current_peer_id": self.peer_id,
                        "listen_for": peer_ids,
                        "data": "connected",
                    }
                )

                offers_sent: Set[int] = set()

                for pid in peer_ids:
                    if pid == self.peer_id:
                        print(f"[{self.peer_id}] Skipping connection to self ({pid})")
                        continue
                    pc = await self._create_peer_connection(pid)

                    if self.peer_id < pid:
                        offers_sent.add(pid)
                        offer = await pc.createOffer()
                        await pc.setLocalDescription(offer)
                        if self._ws and not self._ws.closed:
                            try:
                                await self._ws.send_json(
                                    {
                                        "from": self.peer_id,
                                        "to": pid,
                                        "type": "offer",
                                        "data": {
                                            "sdp": pc.localDescription.sdp,
                                            "type": pc.localDescription.type,
                                        },
                                    }
                                )
                                print(f"[{self.peer_id}] → offer → [{pid}]")
                            except Exception:
                                pass

                # Node's main loop now just processes signaling messages
                while self._running and self._ws and not self._ws.closed:
                    try:
                        msg = await self._ws.receive(timeout=1.0)

                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                payload: Dict[str, Any] = json.loads(msg.data)
                            except json.JSONDecodeError:
                                print(
                                    f"[{self.peer_id}] Error decoding JSON: {msg.data}"
                                )
                                continue

                            frm = payload.get("from")
                            to = payload.get("to")
                            typ = payload.get("type")
                            data = payload.get("data")

                            if to is not None and to != self.peer_id:
                                continue

                            if (
                                frm is None
                                or typ is None
                                or (data is None and typ != "disconnect")
                            ):
                                print(
                                    f"[{self.peer_id}] Warning: Incomplete message: {payload}"
                                )
                                continue

                            pc = self._pcs.get(frm)
                            if not pc and frm in peer_ids:
                                print(
                                    f"[{self.peer_id}] Creating PC for new peer {frm}"
                                )
                                pc = await self._create_peer_connection(frm)
                            elif not pc and typ != "disconnect":
                                continue
                            elif not pc and typ == "disconnect":
                                print(f"[{self.peer_id}] Peer {frm} disconnected.")
                                if frm in self._pcs:
                                    await self._pcs[frm].close()
                                continue

                            # Handle different signaling message types
                            if typ == "offer":
                                if self.peer_id > frm:
                                    print(f"[{self.peer_id}] ← offer ← [{frm}]")
                                    offer = RTCSessionDescription(
                                        sdp=data["sdp"], type=data["type"]
                                    )
                                    await pc.setRemoteDescription(offer)
                                    answer = await pc.createAnswer()
                                    await pc.setAnswer(
                                        answer
                                    )  # Corrected from setLocalDescription
                                    if self._ws and not self._ws.closed:
                                        try:
                                            await self._ws.send_json(
                                                {
                                                    "from": self.peer_id,
                                                    "to": frm,
                                                    "type": "answer",
                                                    "data": {
                                                        "sdp": pc.localDescription.sdp,
                                                        "type": pc.localDescription.type,
                                                    },
                                                }
                                            )
                                            print(
                                                f"[{self.peer_id}] → answer → [{frm}]"
                                            )
                                        except Exception:
                                            pass
                                else:
                                    print(
                                        f"[{self.peer_id}] Warning: Unexpected offer from {frm}"
                                    )

                            elif typ == "answer":
                                if self.peer_id < frm:
                                    print(f"[{self.peer_id}] ← answer ← [{frm}]")
                                    answer = RTCSessionDescription(
                                        sdp=data["sdp"], type=data["type"]
                                    )
                                    await pc.setRemoteDescription(answer)
                                else:
                                    print(
                                        f"[{self.peer_id}] Warning: Unexpected answer from {frm}"
                                    )

                            elif typ == "candidate":
                                try:
                                    candidate = RTCIceCandidate(
                                        sdp=data["candidate"],
                                        sdpMid=data.get("sdpMid"),
                                        sdpMLineIndex=data.get("sdpMLineIndex"),
                                    )
                                    await pc.addIceCandidate(candidate)
                                except Exception as e:
                                    print(
                                        f"[{self.peer_id}] Error adding ICE candidate from {frm}: {e}"
                                    )

                            elif typ == "peer_info" or typ == "connection_opportunity":
                                print(f"[{self.peer_id}] Received {typ} from {frm}")
                                if (
                                    self.peer_id < frm
                                    and frm in peer_ids
                                    and frm not in offers_sent
                                ):
                                    offers_sent.add(frm)
                                    try:
                                        offer = await pc.createOffer()
                                        await pc.setLocalDescription(offer)
                                        if self._ws and not self._ws.closed:
                                            await self._ws.send_json(
                                                {
                                                    "from": self.peer_id,
                                                    "to": frm,
                                                    "type": "offer",
                                                    "data": {
                                                        "sdp": pc.localDescription.sdp,
                                                        "type": pc.localDescription.type,
                                                    },
                                                }
                                            )
                                            print(
                                                f"[{self.peer_id}] → offer → [{frm}] (after {typ})"
                                            )
                                    except Exception:
                                        pass

                            elif typ == "request_offer":
                                print(
                                    f"[{self.peer_id}] Received request_offer from {frm}"
                                )
                                if (
                                    self.peer_id < frm
                                    and frm in peer_ids
                                    and frm in offers_sent
                                ):
                                    try:
                                        offer = await pc.createOffer()
                                        await pc.setLocalDescription(offer)
                                        if self._ws and not self._ws.closed:
                                            await self._ws.send_json(
                                                {
                                                    "from": self.peer_id,
                                                    "to": frm,
                                                    "type": "offer",
                                                    "data": {
                                                        "sdp": pc.localDescription.sdp,
                                                        "type": pc.localDescription.type,
                                                    },
                                                }
                                            )
                                            print(
                                                f"[{self.peer_id}] → offer → [{frm}] (re-sending on request)"
                                            )
                                    except Exception:
                                        pass

                            elif typ == "disconnect":
                                print(f"[{self.peer_id}] Peer {frm} disconnected.")
                                # Cleanup handled in connectionstatechange

                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            print(f"[{self.peer_id}] WebSocket error: {msg.data}")
                            self._running = False
                            break

                        elif msg.type in (
                            aiohttp.WSMsgType.CLOSE,
                            aiohttp.WSMsgType.CLOSED,
                        ):
                            print(f"[{self.peer_id}] WebSocket connection closed.")
                            self._running = False
                            break

                        elif msg.type == aiohttp.WSMsgType.PING:
                            if self._ws and not self._ws.closed:
                                await self._ws.pong()

                        elif msg.type == aiohttp.WSMsgType.PONG:
                            pass

                        else:
                            print(
                                f"[{self.peer_id}] Received unknown message type: {msg.type}"
                            )

                    except asyncio.TimeoutError:
                        continue
                    except aiohttp.WSServerHandshakeError as e:
                        print(f"[{self.peer_id}] WebSocket handshake error: {e}")
                        self._running = False
                        break
                    except Exception as e:
                        print(f"[{self.peer_id}] Error processing message: {e}")
                        await asyncio.sleep(0.1)

            except aiohttp.ClientConnectorError as e:
                print(f"[{self.peer_id}] Connection error to signaling server: {e}")
            except Exception as e:
                print(f"[{self.peer_id}] An unexpected error occurred: {e}")

            finally:
                print(f"[{self.peer_id}] Shutting down...")

                # Close all peer connections
                for pid, pc in list(self._pcs.items()):
                    if not pc.closed:
                        print(f"[{self.peer_id}] Closing connection with {pid}...")
                        await pc.close()
                self._pcs.clear()
                self._chat_outgoing_channels.clear()
                self._chat_incoming_channels.clear()
                self._video_outgoing_channels.clear()
                self._video_incoming_channels.clear()

                # Ensure the WebSocket connection is closed
                if self._ws and not self._ws.closed:
                    await self._ws.close()
                    print(f"[{self.peer_id}] Signaling WebSocket closed.")


# --- Sample Usage (External Control with pyrealsense2) ---


class VideoDisplayManager:
    """Manages decoding and displaying video frames from multiple peers and streams."""

    def __init__(self, my_peer_id: int):
        self.my_peer_id = my_peer_id
        # Store frames keyed by (peer_id, stream_index)
        self._received_video_frames: Dict[Tuple[int, int], np.ndarray] = {}
        self._display_thread: Optional[threading.Thread] = None
        self._running = True
        self._lock = threading.Lock()  # Lock for accessing _received_video_frames
        self._windows_created: Set[Tuple[int, int]] = (
            set()
        )  # Keep track of created windows per (peer, stream)

    def handle_video_frame(
        self, peer_id: int, stream_index: int, frame_data: bytes
    ) -> None:
        """Decodes a video frame and prepares it for display."""
        try:
            np_arr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(
                np_arr, cv2.IMREAD_COLOR
            )  # Assuming BGR or Grayscale for display
            if frame is not None:
                with self._lock:
                    self._received_video_frames[(peer_id, stream_index)] = frame
                self._start_display_thread_if_needed()
            # else: Error decoding is not printed here to keep this handler clean,
            #       can be added for debugging if needed.
        except Exception as e:
            print(
                f"[{self.my_peer_id}] Error processing video frame for stream {stream_index} from {peer_id}: {e}"
            )

    def _start_display_thread_if_needed(self):
        """Starts the display thread if it's not already running."""
        if self._display_thread is None or not self._display_thread.is_alive():
            self._running = True
            self._display_thread = threading.Thread(
                target=self._display_loop, daemon=True
            )
            self._display_thread.start()
            print(f"[{self.my_peer_id}] Video display thread started.")

    def _display_loop(self):
        """Blocking loop for displaying received video frames using OpenCV."""
        print(f"[{self.my_peer_id}] Starting blocking video display loop.")

        while self._running:
            # Get a list of (peer_id, stream_index) tuples that have frames
            frames_to_display = list(self._received_video_frames.keys())

            if not frames_to_display and not self._windows_created:
                cv2.waitKey(1)
                import time

                time.sleep(0.01)
                continue

            peers_streams_with_closed_windows = []
            for peer_id, stream_index in frames_to_display:
                try:
                    with self._lock:
                        frame = self._received_video_frames.get((peer_id, stream_index))

                    if frame is not None:
                        peer_stream_window_name = f"Peer {self.my_peer_id} - Video from {peer_id} (Stream {stream_index})"
                        if (peer_id, stream_index) not in self._windows_created:
                            cv2.namedWindow(peer_stream_window_name, cv2.WINDOW_NORMAL)
                            self._windows_created.add((peer_id, stream_index))

                        cv2.imshow(peer_stream_window_name, frame)

                        if (
                            cv2.getWindowProperty(
                                peer_stream_window_name, cv2.WND_PROP_VISIBLE
                            )
                            < 1
                        ):
                            print(
                                f"[{self.my_peer_id}] Window for peer {peer_id} stream {stream_index} closed manually."
                            )
                            peers_streams_with_closed_windows.append(
                                (peer_id, stream_index)
                            )

                except Exception as e:
                    print(
                        f"[{self.my_peer_id}] Error displaying video frame for stream {stream_index} from {peer_id}: {e}"
                    )
                    peers_streams_with_closed_windows.append((peer_id, stream_index))

            # Clean up resources for peers/streams whose windows were closed
            for peer_id, stream_index in peers_streams_with_closed_windows:
                with self._lock:
                    if (peer_id, stream_index) in self._received_video_frames:
                        del self._received_video_frames[(peer_id, stream_index)]
                # Note: Closing the PC is handled in the Node's connectionstatechange
                # when the peer disconnects entirely, not per stream window close.
                if (peer_id, stream_index) in self._windows_created:
                    cv2.destroyWindow(
                        f"Peer {self.my_peer_id} - Video from {peer_id} (Stream {stream_index})"
                    )
                    self._windows_created.remove((peer_id, stream_index))

            # Process OpenCV events and check for quit key
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                print(
                    f"[{self.my_peer_id}] 'q' pressed in OpenCV window, signaling shutdown."
                )
                self._running = False  # Signal shutdown

            # If there are no more windows but _running is still True and we had frames, assume manual close
            if (
                self._running
                and not self._windows_created
                and self._received_video_frames
            ):
                print(
                    f"[{self.my_peer_id}] No video windows visible, assuming manual close and signaling shutdown."
                )
                self._running = False

            import time

            time.sleep(0.01)

        print(f"[{self.my_peer_id}] Blocking video display loop stopping.")
        cv2.destroyAllWindows()  # Ensure all windows are closed when the loop finishes
        print(f"[{self.my_peer_id}] OpenCV windows destroyed.")

    def stop(self):
        """Signals the display thread to stop and cleans up."""
        self._running = False
        if self._display_thread and self._display_thread.is_alive():
            cv2.waitKey(1)  # Attempt to unblock waitKey
            try:
                self._display_thread.join(timeout=1.0)
            except threading.TimeoutError:
                print(
                    f"[{self.my_peer_id}] Warning: Display thread did not join within timeout."
                )

        cv2.destroyAllWindows()  # Ensure windows are closed


# --- External Functions for Handling Input and Video Capture (using pyrealsense2) ---


async def handle_user_input(node: Node):
    """Reads user input and sends chat messages via the node."""
    print(f"[{node.peer_id}] Enter messages to broadcast. Type 'quit' to exit.")
    loop = asyncio.get_event_loop()
    while True:
        try:
            # Use a small timeout or check self._running to allow graceful exit
            msg = await asyncio.wait_for(
                loop.run_in_executor(None, input, f"[{node.peer_id}] Chat Broadcast: "),
                timeout=0.1,  # Check for shutdown every 0.1 seconds
            )

            if msg.strip().lower() == "quit":
                break  # Signal main loop to stop

            if not msg.strip():
                continue

            await node.send_chat_message(msg)

        except asyncio.TimeoutError:
            # Input timed out, check if we should stop
            if not node._running:
                break
            continue  # Continue waiting for input

        except Exception as e:
            print(f"[{node.peer_id}] Error getting user input or sending chat: {e}")
            await asyncio.sleep(0.1)
            if not node._running:
                break


# Define a type for stream configurations
# Tuple format: (stream_type, width, height, fps, format_type, stream_index_in_realsense)
# stream_type: rs.stream enum (e.g., rs.stream.color, rs.stream.fisheye)
# format_type: rs.format enum (e.g., rs.format.bgr8, rs.format.y8)
# stream_index_in_realsense: 0 or 1 for stereo/fisheye, usually 0 for color/depth
RealsenseStreamConfig = Tuple[rs.stream, int, int, int, rs.format, int]


async def run_realsense_stream_and_send(
    node: Node, stream_config: RealsenseStreamConfig, stream_index: int
):
    """
    Captures video frames from a specific pyrealsense2 stream configuration
    and sends them via the node.
    """
    stream_type, width, height, fps, format_type, stream_index_in_realsense = (
        stream_config
    )
    print(
        f"[{node.peer_id}] Starting Realsense stream {stream_index} with config: {stream_config}"
    )

    pipeline = rs.pipeline()
    config = rs.config()

    # Configure the stream
    try:
        config.enable_stream(
            stream_type, stream_index_in_realsense, width, height, format_type, fps
        )
        print(
            f"[{node.peer_id}] Configured stream: Type={stream_type}, Index={stream_index_in_realsense}, Resolution={width}x{height}, FPS={fps}, Format={format_type}"
        )
    except Exception as e:
        print(
            f"[{node.peer_id}] Error configuring Realsense stream {stream_index} with config {stream_config}: {e}"
        )
        print(
            f"[{node.peer_id}] Make sure the specified stream configuration is supported by a connected Realsense device."
        )
        return  # Exit task if configuration fails

    # Find a device that supports the configured stream
    try:
        pipeline.start(config)
        print(f"[{node.peer_id}] Realsense pipeline started for stream {stream_index}.")
    except Exception as e:
        print(
            f"[{node.peer_id}] Error starting Realsense pipeline for stream {stream_index}: {e}"
        )
        print(f"[{node.peer_id}] Ensure a compatible Realsense device is connected.")
        return  # Exit task if pipeline fails to start

    # Determine the pixel format for encoding
    # OpenCV imencode works well with BGR or Grayscale (CV_8U)
    # Realsense formats like Z16 (depth) or Y16 need conversion before encoding
    needs_color_conversion = False
    if format_type == rs.format.y8:  # Grayscale 8-bit
        needs_color_conversion = True
        print(
            f"[{node.peer_id}] Stream {stream_index} format is Y8, will convert to BGR for encoding/display."
        )
    elif format_type == rs.format.bgr8:  # BGR 8-bit
        pass  # No conversion needed
    elif format_type == rs.format.rgb8:  # RGB 8-bit
        needs_color_conversion = True  # Convert to BGR
        print(
            f"[{node.peer_id}] Stream {stream_index} format is RGB8, will convert to BGR for encoding/display."
        )
    elif format_type == rs.format.z16:  # Depth 16-bit
        print(
            f"[{node.peer_id}] Warning: Streaming raw Z16 depth data for stream {stream_index}. Displaying this directly might not work as expected."
        )
        # You might want to add depth-to-colormap conversion here before encoding
        pass  # Send raw Z16 for now, display manager might fail or show garbage
    else:
        print(
            f"[{node.peer_id}] Warning: Streaming unsupported Realsense format {format_type} for stream {stream_index}. Encoding/display might fail."
        )
        pass  # Attempt to send raw data

    try:
        while True:  # Loop indefinitely until cancelled
            # Wait for a coherent set of frames
            frames = pipeline.wait_for_frames()
            # Get the specific frame for this stream configuration
            frame = frames.get_stream(
                stream_type, stream_index_in_realsense
            ).as_video_frame()

            # Convert frame to numpy array
            frame_data_np = np.asanyarray(frame.get_data())

            # Perform color conversion if needed
            if needs_color_conversion:
                if format_type == rs.format.y8:
                    frame_data_np = cv2.cvtColor(frame_data_np, cv2.COLOR_GRAY2BGR)
                elif format_type == rs.format.rgb8:
                    frame_data_np = cv2.cvtColor(frame_data_np, cv2.COLOR_RGB2BGR)

            # Encode the frame (NumPy array) to JPEG bytes
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 60]
            _, buffer = cv2.imencode(".jpg", frame_data_np, encode_param)
            frame_data_bytes = buffer.tobytes()

            # Send the encoded frame data via the node
            await node.send_video_frame(stream_index, frame_data_bytes)

            # No need for explicit sleep here, wait_for_frames() blocks until a frame is ready
            # which implicitly controls the frame rate based on the camera's FPS setting.

    except asyncio.CancelledError:
        print(f"[{node.peer_id}] Realsense stream task {stream_index} cancelled.")
    except Exception as e:
        print(f"[{node.peer_id}] Error in Realsense stream task {stream_index}: {e}")
    finally:
        print(
            f"[{node.peer_id}] Realsense pipeline stopping for stream {stream_index}."
        )
        pipeline.stop()
        print(f"[{node.peer_id}] Realsense pipeline stopped for stream {stream_index}.")


async def main():
    print("\n--- Running Sample Usage with External Control (pyrealsense2) ---")
    peer_id = int(input("Enter your peer ID: "))
    listen_for = list(
        map(int, input("Enter target peer IDs (space-separated): ").split())
    )

    # --- Configure Realsense Streams to Send ---
    stream_video_input = input(
        "Do you want to stream video from this node? (yes/no): "
    ).lower()
    is_streaming = stream_video_input == "yes"

    streams_to_send_configs: List[RealsenseStreamConfig] = []
    if is_streaming:
        # Define the configurations for the streams this node will capture and send.
        # Each tuple is (stream_type, width, height, fps, format_type, stream_index_in_realsense)
        # Example for two Fisheye streams from a T265:
        # Make sure your device supports these settings.
        print(
            "Configuring to stream two Fisheye streams from Realsense (T265 example)."
        )
        streams_to_send_configs = [
            (rs.stream.fisheye, 640, 480, 30, rs.format.y8, 1),  # Stream 0 (Fisheye 1)
            (rs.stream.fisheye, 640, 480, 30, rs.format.y8, 2),  # Stream 1 (Fisheye 2)
        ]

        # Example for Color and Depth streams from a D400 series (Depth requires special handling for display)
        # Uncomment and modify if using a D400 series camera
        # print("Configuring to stream Color and Depth streams from Realsense (D400 example).")
        # streams_to_send_configs = [
        #     (rs.stream.color, 640, 480, 30, rs.format.bgr8, 0), # Stream 0 (Color)
        #     (rs.stream.depth, 640, 480, 30, rs.format.z16, 0)  # Stream 1 (Depth - likely needs conversion before sending/display)
        # ]

        if not streams_to_send_configs:
            print("No Realsense stream configurations defined for streaming.")
            is_streaming = False  # Disable streaming if no configs

    num_streams_to_send = len(streams_to_send_configs)

    # The number of video streams the node should be prepared to handle (receive)
    # should match the maximum number of streams that *any* peer it connects to
    # might send. This is a simplification. A real system needs better stream negotiation.
    # For this example, let's assume if this node is sending N streams,
    # it's also prepared to receive N streams from each peer.
    # If this node is NOT sending streams, let's assume it expects 2 streams from peers
    # if it's listening for any peers.
    num_streams_to_handle = num_streams_to_send
    if num_streams_to_send == 0 and listen_for:
        num_streams_to_handle = (
            2  # Assume peers might send 2 streams if we're not sending
        )

    node = Node(peer_id, num_video_streams=num_streams_to_handle)
    video_display_manager = VideoDisplayManager(peer_id)

    # Assign custom handler functions to the public methods
    def custom_chat_handler(pid: int, msg: str) -> None:
        print(f"[ChatHandler {node.peer_id}] Chat from {pid}: {msg}")

    def custom_video_handler(pid: int, stream_index: int, frame_data: bytes) -> None:
        # Pass the data and stream index to the external manager
        video_display_manager.handle_video_frame(pid, stream_index, frame_data)

    node.on_chat_message_received = custom_chat_handler
    node.on_video_stream_data_received = custom_video_handler

    # Create tasks for handling input and video capture (if streaming)
    input_task = asyncio.create_task(handle_user_input(node))
    video_capture_tasks = []
    if is_streaming:
        for i, stream_config in enumerate(streams_to_send_configs):
            video_capture_tasks.append(
                asyncio.create_task(
                    run_realsense_stream_and_send(node, stream_config, i)
                )
            )

    try:
        # Run the node's connection logic and the external tasks concurrently
        await asyncio.gather(
            node.connect_to(listen_for),
            input_task,
            *video_capture_tasks,  # Unpack the list of video capture tasks
            return_exceptions=True,  # Allow other tasks to run if one fails
        )
    except KeyboardInterrupt:
        print("Sample shutting down from KeyboardInterrupt...")
    finally:
        print("Main loop finished. Starting cleanup...")
        # Signal the external tasks to stop
        input_task.cancel()
        for task in video_capture_tasks:
            task.cancel()

        # Wait for external tasks to finish
        try:
            await asyncio.gather(
                input_task, *video_capture_tasks, return_exceptions=True
            )
        except asyncio.CancelledError:
            pass  # Expected cancellation

        # Signal the video display manager to stop its thread
        video_display_manager.stop()

        # The node's cleanup is handled within its connect_to method's finally block
        print("Cleanup complete.")


if __name__ == "__main__":
    asyncio.run(main())

    # To run multiple nodes simultaneously, you'll need to open multiple terminal windows
    # and run this script in each.
    # Answer 'yes' or 'no' when asked if you want to stream video.
    # If streaming, the code is configured by default for T265 fisheye streams.
    # Modify 'streams_to_send_configs' in the main function for different Realsense devices/streams.
    # Provide unique peer IDs and the IDs of peers they should listen for.
