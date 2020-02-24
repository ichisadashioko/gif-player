#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char *argv[])
{
    printf("argc: %d\n", argc);

    for (int i = 0; i < argc; i++)
    {
        printf("%s\n", argv[i]);
    }

    if (argc < 2)
    {
        printf("Require input file\n");
        return 1;
    }

    char ch;
    char *filePath = argv[1];
    FILE *fp;

    printf("Input file path is %s\n", filePath);

    if (access(filePath, F_OK) == -1)
    {
        // file doesn't exist
        printf("File %s does not exist!\n", filePath);
        return 1;
    }

    // open file in read mode
    fp = fopen(filePath, "r");

    if (fp == NULL)
    {
        perror("Error while opening the file.\n");
        return 1;
    }

    // seek to the end of file to get file size
    fseek(fp, 0, SEEK_END);
    long fileLen = ftell(fp);

    while ((ch = fgetc(fp)) != EOF)
    {
        printf("%d", ch);
    }

    fclose(fp);

    return 0;
}