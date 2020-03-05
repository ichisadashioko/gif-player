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

Now we enter the main loop of the algorithm. We read the next index in the index stream, 1, into K [Step 1]. Next we see if we have a record for the index buffer plus K in the code stream. In this case we looking for 1,1. Currently our code table only contains single colors so this value is not in there. Now we will actually add a new row to our code table that does contain this value. The next available code is #6 be 1,1. Not that we do not actually send this code to the code stream, instead we send just the code for the value(s) in the index buffer. This index buffer is just 1 and the code for 1 is #1. This is the code we output. We now reset the index buffer to just the value of K and K becomes nothing. [Step 2].

We continue by reading the next index into K. [Step 3]. Now K is 1 and the index buffer is 1. Again we look to see if there is a value in our code table for the buffer plus K (1,1) and this time there is. (In fact we just added it.) Therefore we add K to the end of the index buffer and clear out K. Now our index buffer is 1,1. [Step 4].

The next index in the index stream is yet another  1. This our new K [Step 5]. Now the index buffer plus K is (1,1,1) which we do not have a code for in our code table. As we did before, we define a new code and add it to the code table. The next code would be #7; thus #7 = (1,1,1). Now we kick out the code for just the values in the index buffer(#6 = (1,1)) to the code stream and set the index buffer to K. [Step 6].

As you can see we dynamically built many new codes for our code table as we compressed the data. For large files this can turn into a large number of codes. It turns out that the GIF format specifies a maximum code of #4095 (this happens to be the largest 12-bit number). If you want to use a new code. you have to clear out all of your old codes. You do this by sending the clear code (which for our sample was the #4). This tells the decoder that you are re-initializing  your code table and it should too. Then you start building your own codes again starting just after the value of your end-of-information code (in our sample, we would start again at #6).

# LZW Decompression

At some point we will probably need to turn this code stream back into a picture. To do this, we only need to know the values in the stream and the size of the color table that was used. That's it. You remember that big code table we built during compression? We actually have enough information in the code stream itself to be able to rebuilt it.

Again, I'll list the algorithm and then we will walk though an example. Let me define a few terms I will be using. `CODE` will be the current code we're working with. `CODE-1` will be the code just before `CODE` in the code stream.


# Steps from specification

The conversion of the image from a series of pixel values to a transmitted or stored character stream involves several steps. In brief these steps are:

1. Establish the Code Size - Define the number of bits needed to represent the actual data.

2. Compress the Data - Compress the series of image pixels to a series of compression codes.

3. Build a Series of Bytes - Take the set of compression codes and convert to a string of 8-bit bytes.

4. Package the Bytes - Package sets of bytes into blocks preceded by character counts and output.
