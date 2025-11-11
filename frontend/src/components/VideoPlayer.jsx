import { useEffect, useRef } from "react";
import { API } from "../App";
import Hls from "hls.js";

const VideoPlayer = ({ video }) => {
  const videoRef = useRef(null);
  const hlsRef = useRef(null);

  useEffect(() => {
    if (!videoRef.current || !video) return;

    const videoElement = videoRef.current;
    const videoSrc = `${API}/stream/hls/${video.id}/playlist.m3u8`;

    if (Hls.isSupported()) {
      const hls = new Hls({
        enableWorker: true,
        lowLatencyMode: true,
      });

      hls.loadSource(videoSrc);
      hls.attachMedia(videoElement);

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        videoElement.play().catch((e) => console.log("Auto-play prevented:", e));
      });

      hlsRef.current = hls;

      return () => {
        if (hlsRef.current) {
          hlsRef.current.destroy();
        }
      };
    } else if (videoElement.canPlayType("application/vnd.apple.mpegurl")) {
      videoElement.src = videoSrc;
      videoElement.addEventListener("loadedmetadata", () => {
        videoElement.play().catch((e) => console.log("Auto-play prevented:", e));
      });
    }
  }, [video]);

  return (
    <div className="w-full aspect-video bg-black rounded-lg overflow-hidden">
      <video
        ref={videoRef}
        controls
        className="w-full h-full"
        data-testid="video-player"
      />
    </div>
  );
};

export default VideoPlayer;
