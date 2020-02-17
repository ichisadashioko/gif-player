# [Inside the GIF file format](https://commandlinefanatic.com/cgi-bin/showarticle.cgi?article=art011)

Last month, I presented a breakdown of the LZW algorithm, which is the compression algorithm behind the GIF (Graphics Interchange Format) image format. I stopped short of presenting the actual GIF format itself there - this article will present a full-fledged GIF decoder, using the LZW decompressor I developed last month.

GIF itself is 25 years old, the oldest image compression format still in common use. Although it has competition from the popular PNG and JPG formats, it still remains a fairly common image compression method. As you'll see, a lot of the design considerations behind the GIF format were based on the hardware of the time which itself is now archaically out-of-date, but the format in general has managed to stand the test of time.

An `image`, in the context of a GIF file anyway, is a rectangular array of colored dots called `pixels`. Because of the way CRT (`Cathode-Ray Tube`) displays and their modern successors, the Liquid Crytal Display (LCD) are built, these pixels are actually combinations of three separate color components; one red, one green and one blue. By varying the intensity of the individual color components for each pixel, any color can be represented. Deep purple, for example, is a mix of full-intensity red and full-intensity blue. Generally speaking, the color components can vary from 0 (not present) to 2<sup>8</sup>=256 (full intensity).

Early color-capable graphics hardware could only display 16 distinct colors at a time, but modern displays can display any combination of red, green and blue intensities. This works out to 2<sup>16</sup>=16,777,216 distinct colors at one time - far, far more than human eye can actually discern. Since GIF dates back to the 1980's, when 16-color displays were common and 2<sup>24</sup> "true color" displays were rare, GIF is based on the notion of `palettes`, which the specification refers to as `color tables`. Although a 16-color display could only display 16 distinct colors _at one time_, the foremost app was allowed to select 16 colors (of the 2<sup>24</sup> possible color component intensity combinations) these were. The GIF file format, then, starts off by describing a `palette` of these color intensity values; the image itself is then described as a series of indices into this color palette.

![](./images/art0111.png)

Color Table:

|Index|Red|Green|Blue|
|-----|---|-----|----|
|0|0|0|0|
|1|0|255|255|
|2|0|0|255|
|3|128|0|0|

__Example 1__ Indexed four-color smiley face image

Example 1 illustrates a crudely-drawn face image. Since it only has four colors, it only needs four palette entries. These palette entries are drawn from a large color space, but each pixel here can be represented using 2 bits.

This "palettizing" of the image's pixels compresses it quite a bit. It would take 3 bytes per pixel to describe an image in true-color format; by palettizing an image this way, the size of a 16-color image can be immediately reduced by a factor of 6, since it only takes 4 bits to describe each pixel. More distinct colors means less compression, but 256 colors is quite a few, and even a 256 color palette represents a 3:1 compression ratio.