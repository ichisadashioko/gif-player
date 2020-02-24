#include <stdio.h>
#include <stdlib.h>

typedef struct
{
    unsigned short width;
    unsigned short height;
    unsigned char fields;
    unsigned char background_color_index;
    unsigned char pixel_aspect_ratio;
} screen_descriptor_t;

/**
 * @param gif_file the file descriptor of a file containing a
 * GIF-encoded. This should point to the first byte in
 * the file when invoked.
 */
static void process_gif_stream(int gif_file)
{
    unsigned char header[7];
    screen_descriptor_t screen_descriptor;
    int color_resolution_bits;

    // A GIF file starts with a Header (section 17)
    if (read(gif_file, header, 6) != 6)
    {
        perror("Invalid GIF  file (too short)");
        return;
    }

    header[6] = 0x0;

    // XXX there's another format, GIF87a, that you may still find
    // floating around.
    if (strcmp("GIF89a", header))
    {
        fprintf(stderr, "Invalid GIF file (header is '%s', should be 'GIF89a')\n", header);
        return;
    }

    // Followed by a logical screen descriptor
    // Note that this works because GIFs specify little-endian order; on a
    // big-endian machine, the height & width would need to be reversed.

    // Can't use sizeof here since GCC does byte alignment;
    // sizeof( screen_descriptor_t ) = 8!
    if (read(gif_file, &screen_descriptor, 7) < 7)
    {
        perror("Invalid GIF file (too short)");
        return;
    }

    color_resolution_bits = ((screen_descriptor.fields & 0x70) >> 4) + 1;
}
