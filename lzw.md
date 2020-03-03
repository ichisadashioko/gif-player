# LZW Compression

LZW compression is used in GIF files to reduce file size. (Actually it is a slight variation from the standard LZW for use in GIF images.) This method requires building a __code table__. This code table will allow us to use special codes to indicate a sequence of colors rather than just one at a time. The first thing we do is to _initialize the code table_. We start by adding a code for each of the colors in the color table. We start by adding a code for each of the colors in the table. This would be a local color table if one was provided, or the global color table. (I will be starting all codes with "#" to distinguish them from color indies.)

| Code | Color(s) |
|---|---|
| #0 | 0 |
| #1 | 1 |
| #2 | 2 |
| #3 | 3 |
| #4 | Clear Code |
| #5 | End Of Information Code |

I added a code for each of the colors in the global color table of our sample image. I also snuck in two special control codes. (These special codes are only used in the GIF version of LZW, not in standard LZW compression.) Our code table is now considered initialized.

Let me now explain what those special codes are for. The first new code is the _clear code_ (CC). Whenever you come across the clear code in the image data, it's your cue to reinitialize the code table. (I'll explain why you might need to do this in a bit.) The second new code is the _end of information code_ (EOI). When you come across this code, this means you've reached the end of the image. Here I've placed the special codes right after the color codes, but actually the value of the special codes depends on the value of the LZW minimum code size from the image data block. If the LZW minimum code size is the same as the color table size, then special codes immediately follow the colors; however it is possible to specify a larger LZW minimum code size which may leave a gap in the codes where no colors are assigned. This can be summarized in the following table.

| LZW Min Code Size | Color Codes | Clear Code | EOI Code |
|-------------------|-------------|------------|----------|
| 2 | #0-#3 | #4 | #5 |
| 3 | #0-#7 | #8 | #9 |
| 4 | #0-#15 | #16 | #17 |
| 5 | #0-#31 | #32 | #33 |
| 6 | #0-#63 | #64 | #65 |
| 7 | #0-#127 | #128 | #129 |
| 8 | #0-#255 | # 256 | #257 |

Before we proceed, let me define two more terms. First the __index stream__ will be the list of indies of the color for each of the pixels. This is the input we will be compressing. The __code stream__ will be the list of codes we generate as output. The __index buffer__ will be the list of color indies we care "currently looking at". The index buffer will contain a list of one or more color indies. Now we can step though the LZW compression algorithm. First, I'll just list the steps. After that I'll walk through the steps with our specific example.

- Initialize code table
- Always start by sending a clear code to the code stream.
- Read first index from index stream. This value is now the value for the index buffer.
- &lt;LOOP POINT&gt;
- Get the next index from the index stream to the index buffer. We will call this index, K
- Is index buffer + K in our code table?
- Yes:
    - Add K to the end of the index buffer
    - If there are more indies, return to LOOP POINT
- No:
    - Add a row for index buffer + K into our code table with the next smallest code
    - Output the code for just the index buffer to our code stream
    - Index buffer is set to K
    - K is set to nothing
    - If there are more indies, return to LOOP POINT
- Output code for contents of index buffer
- Output end-of-information code

Seems simple enough, right? It really isn't all that bad. Let's walk though our sample image to show you how this works. (The steps I will be describing are summarized in the following table. Numbers highlighted in green are in the index buffer; numbers in purple are the current K value.) We have already initialized our code table. We start by doing two things: we output our clear code (#4) to the code stream, and we read the first color index from index stream, 1, into our index buffer [Step 0].

Now we enter the main loop of the algorithm. We read the next index in the index stream, 1, into K [Step 1]. Next we see if we have a record for the index buffer plus K in the code stream. In this case we looking for 1,1. Currently our code table only contains single colors so this value is not in there. Now we will actually add a new row to our code table that does contain