import { useEffect, useRef, useState } from "react";
import axios from "axios";
import { API } from "../App";
import Hls from "hls.js";

const VideoPlayer = ({ video }) => {
  const videoRef = useRef(null);
  const hlsRef = useRef(null);
  const [captions, setCaptions] = useState([]);

  // Fetch caption tracks for this video
  useEffect(() => {
    if (!video?.id) return;
    let cancel = false;
    axios
      .get(`${API}/videos/${video.id}/captions`)
      .then((r) => {
        if (!cancel) setCaptions(r.data.items || []);
      })
      .catch(() => {});
    return () => {
      cancel = true;
    };
  }, [video?.id]);

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
        crossOrigin="anonymous"
        className="w-full h-full"
        data-testid="video-player"
      >
        {captions.map((c) => (
          <track
            key={c.id}
            kind="subtitles"
            src={`${API}/captions/${c.id}`}
            srcLang={c.language}
            label={c.label || c.language.toUpperCase()}
            default={c.is_default}
            data-testid={`caption-track-${c.id}`}
          />
        ))}
      </video>
    </div>
  );
};

export default VideoPlayer;
