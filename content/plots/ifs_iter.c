#include <stdlib.h>
#include <math.h>

typedef struct _Point
{
    double x;
    double y;
} Point;

void ifs_iter(Point *point, int n, double *eqs, int *ps, int neq, int *count, int width, int height)
{
    int max_p, r;
    double x, y, x2, y2;
    int xi, yi;

    max_p = ps[neq - 1];
    x = point->x;
    y = point->y;

    for (int i = 0; i < n; i++)
    {
        int j;
        double *eq;
        double a, b, c, d, e, f;
        r = rand() % max_p;
        for (j = 0; j < neq; j++)
        {
            if (r <= ps[j])
            {
                break;
            }
        }
        eq = eqs + (j * 6);
        a = eq[0];
        b = eq[1];
        c = eq[2];
        d = eq[3];
        e = eq[4];
        f = eq[5];

        x2 = a * x + b * y + c;
        y2 = d * x + e * y + f;
        if(fabs(x2) > 1e5 || fabs(y2) > 1e5){
            break;
        }

        x = x2;
        y = y2;
        xi = (int)x;
        yi = (int)y;

        if (xi >= 0 && xi < width && yi >= 0 && yi < height)
        {
            count[yi * width + xi]++;
        }
    }

    point->x = x;
    point->y = y;
}

void paint_image(int *count, unsigned char * cmap, unsigned char * image, int width, int height)
{
    int i;
    unsigned char * c;
    int max_count = 0;
    double max_tmp;
    int idx;
    for(i = 0; i < width * height; i++){
        if(max_count < count[i]){
            max_count = count[i];
        }
    }

    max_tmp = log(max_count + 1);

    for(i = 0; i < width * height; i++){
        idx = (int)(log(count[i] + 1) / max_tmp * 255);
        if(idx < 0) idx = 0;
        else if(idx >= 255) idx = 255;
        c = &cmap[idx * 3];
        image[i * 3 + 0] = c[0];
        image[i * 3 + 1] = c[1];
        image[i * 3 + 2] = c[2];
     }
}
