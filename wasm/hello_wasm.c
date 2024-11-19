#include <emscripten.h>
#include <stdlib.h>
#include <stdio.h>

#define MAX_FACTORS 32

typedef struct {
    int factors[MAX_FACTORS];
    int count;
} FactorResult;

EMSCRIPTEN_KEEPALIVE
void factorize(int n, FactorResult* result) {
    printf("n = %d\n", n);
    result->count = 0;
    if (n < 2) return;

    for (int i = 2; i * i <= n && result->count < MAX_FACTORS; i++) {
        while (n % i == 0 && result->count < MAX_FACTORS) {
            result->factors[result->count++] = i;
            n /= i;
            printf("i = %d\n", i);
        }
    }
    if (n > 1 && result->count < MAX_FACTORS) {
        result->factors[result->count++] = n;
        printf("i = %d\n", n);
    }
}
