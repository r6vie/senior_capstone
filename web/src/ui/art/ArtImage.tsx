import { useLayoutEffect, useRef, useState } from "react";

/** A book's picture, kept hidden until it has fully arrived: on a slow connection it then appears whole instead
 *  of being drawn in strip by strip over the cover or page. One that fails shows nothing, as before. */
export function ArtImage({ className, src }: { className: string; src: string }) {
  const image = useRef<HTMLImageElement>(null);
  const [arrived, setArrived] = useState<string | null>(null);
  // Before paint: a picture already in the cache never shows hidden, even for a frame.
  useLayoutEffect(() => {
    if (image.current?.complete) setArrived(src);
  }, [src]);
  return (
    <img
      ref={image}
      className={className}
      src={src}
      alt=""
      data-pending={arrived === src ? undefined : "true"}
      onLoad={() => setArrived(src)}
      onError={() => setArrived(src)}
    />
  );
}
