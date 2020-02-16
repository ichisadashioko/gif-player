The gif decoder with accept the byte buffer data and processing it.

- gif header:

| size | description | sample values |
|------|-------------|---------------|
| 3 bytes | ID tag | `GIF` |
| 3 bytes | Version | `87a` `89a` |
| 2 bytes | width |  |
| 2 bytes | height |  |
| 1 byte | field |  |
| 1 byte | background color index |  |
| 1 byte | pixel aspect ratio |  |