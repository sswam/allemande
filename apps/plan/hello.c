#include <emscripten.h>
#include <stdlib.h>

#define MAX_FACTORS 32

typedef struct {
    int factors[MAX_FACTORS];
    int count;
} FactorResult;

EMSCRIPTEN_KEEPALIVE
FactorResult factorize(int n) {
    FactorResult result = {{0}, 0};
    if (n < 2) return result;

    for (int i = 2; i * i <= n && result.count < MAX_FACTORS; i++) {
        while (n % i == 0 && result.count < MAX_FACTORS) {
            result.factors[result.count++] = i;
            n /= i;
        }
    }
    if (n > 1 && result.count < MAX_FACTORS) {
        result.factors[result.count++] = n;
    }
    return result;
}
