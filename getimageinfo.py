# from io import BytesIO
import io
import struct

def getImageInfo(data):
    olddata = str(data)
    data = bytes(data)
    size = len(data)
    height = -1
    width = -1
    content_type = ''

    # handle GIFs
    if (size >= 10) and data[:6] == b'GIF89a':
        # Check to see if content_type is correct
        content_type = 'image/gif'
        w, h = struct.unpack("<HH", data[6:10])
        width = int(w)
        height = int(h)

    # See PNG 2. Edition spec (http://www.w3.org/TR/PNG/)
    # Bytes 0-7 are below, 4-byte chunk length, then 'IHDR'
    # and finally the 4-byte width, height
    elif ((size >= 24) and data[:8] == b'\211PNG\r\n\032\n'
          and (data[12:16] == b'IHDR')):
        w, h = struct.unpack(">LL", data[16:24])
        width = int(w)
        height = int(h)

    # Maybe this is for an older PNG version.
    elif (size >= 16) and data[:8] == b'\211PNG\r\n\032\n':
        # Check to see if we have the right content type
        w, h = struct.unpack(">LL", data[8:16])
        width = int(w)
        height = int(h)

    # handle JPEGs
    elif (size >= 2) and data[:2] == b'\377\330':
        jpeg = io.BytesIO(data)

        jpeg.read(2)
        b = jpeg.read(1)

        try:
            while (b != b''):
                while (b != b'\xFF'): b = jpeg.read(1)
                while (b == b'\xFF'): b = jpeg.read(1)
                if (b >= b'\xC0' and b <= b'\xC3'):
                    jpeg.read(3)
                    h, w = struct.unpack(">HH", jpeg.read(4))
                    break
                else:
                    jpeg.read(int(struct.unpack(">H", jpeg.read(2))[0])-2)
                b = jpeg.read(1)
            width = int(w)
            height = int(h)
        except struct.error:
            pass
        except ValueError:
            pass

    return width, height
