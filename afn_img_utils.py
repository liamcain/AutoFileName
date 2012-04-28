# 
#  These methods were taken from 
#  Zencoding utils (I don't own them)
# 

def char_at(text, pos):
    """
    Returns character at specified index of text.
    If index if out of range, returns empty string
    """
    return text[pos] if pos < len(text) else ''


def get_image_size(stream):
    """
    Gets image size from image byte stream.
    @author http://romeda.org/rePublish/
    @param stream: Image byte stream (use <code>zen_file.read()</code>)
    @type stream: str
    @return: dict with <code>width</code> and <code>height</code> properties
    """
    png_magic_num = "\211PNG\r\n\032\n"
    jpg_magic_num = "\377\330"
    gif_magic_num = "GIF8"
    pos = [0]

    def next_byte():
        char = char_at(stream, pos[0])
        pos[0] += 1
        return ord(char)

    if stream.startswith(png_magic_num):
        # PNG. Easy peasy.
        pos[0] = stream.find('IHDR') + 4

        return {
            'width':  (next_byte() << 24) | (next_byte() << 16) | (next_byte() <<  8) | next_byte(),
            'height': (next_byte() << 24) | (next_byte() << 16) | (next_byte() <<  8) | next_byte()
        }

    elif stream.startswith(gif_magic_num):
        pos[0] = 6

        return {
            'width': next_byte() | (next_byte() << 8),
            'height': next_byte() | (next_byte() << 8)
        }

    elif stream.startswith(jpg_magic_num):
        hex_list = ["%02X" % ord(ch) for ch in stream]

        for k in range(len(hex_list) - 1):
            if hex_list[k] == 'FF' and (hex_list[k + 1] == 'C0' or hex_list[k + 1] == 'C2'):
                #print k, hex(k)  # test
                return {
                    'height': int(hex_list[k + 5], 16) * 256 + int(hex_list[k + 6], 16),
                    'width': int(hex_list[k + 7], 16) * 256 + int(hex_list[k + 8], 16)
                }
    else:
        return {
            'width': -1,
            'height': -1
        }