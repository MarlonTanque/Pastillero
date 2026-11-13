#define PASTILLERO_HOST_TEST 1
#include "../firmware/PastilleroESP32/PastilleroESP32.ino"
#include <stdio.h>
#include <stdlib.h>
int main(int argc, char** argv) {
    if (argc != 9)
        return 2;
    puts(pill::commandDecision(argv[1], argv[2], atoi(argv[3]) != 0, strtoll(argv[4], nullptr, 10),
                               strtoll(argv[5], nullptr, 10), strtoll(argv[6], nullptr, 10),
                               atoi(argv[7]), atoi(argv[8])));
}
