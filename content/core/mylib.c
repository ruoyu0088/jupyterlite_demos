#include <stddef.h>
#include <math.h>

double hypot(double a, double b)
{
    return sqrt(a * a + b * b);
}

double mysum(double * arr, int n)
{
    int i;
    double sum = 0;
    for(i=0;i<n;i++){
        sum += arr[i];
    }
    return sum;
}

typedef struct _IIR2
{
    float b0, b1, b2;
    float a1, a2;
    float z0, z1;
} IIR2;

void iir2_init(IIR2 * self)
{
    self->z0 = 0;
    self->z1 = 0;
}

float iir2_step(IIR2 * self, float x)
{
    float y;
    y = self->b0 * x + self->z0;
    self->z0 = self->b1 * x + self->z1 - self->a1 * y;
    self->z1 = self->b2 * x - self->a2 * y;
    return y;
}

void iir2_run(IIR2 * self, float * x, float * y, size_t n)
{
    size_t i;
    for(i=0;i<n;i++){
        y[i] = iir2_step(self, x[i]);
    }
}
