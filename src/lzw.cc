#include <stdlib.h>
#include <stdio.h>

int main()
{
    // in the beginning God created the heavens and the earth
    char **dictionary;
    int dictionary_ind;
    // pre-initialize the first 255 entries with their own values
    for (dictionary_ind = 0; dictionary_ind < 256; dictionary_ind++)
    {
        dictionary[dictionary_ind] = (char *)malloc(2);
        sprintf(dictionary[dictionary_ind], "%c", dictionary_ind);
    }
    return 0;
}