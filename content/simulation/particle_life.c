#include <math.h>

typedef struct _Particle
{
    float px;
    float py;
    float vx;
    float vy;
    float fx;
    float fy;
    int type;
    int index;
} Particle;

void particles_update(Particle *p, int n, float *gravity, float *radius,
                      int n_color, int width, int height, float edge_strength, float viscosity, float time_scale)
{

    int i, j;
    Particle *p1, *p2;

    for (i = 0; i < n; i++)
    {
        for (j = 0; j < n; j++)
        {
            float dx, dy, r, d;
            int index;
            if (j == i)
                continue;
            p1 = &p[i];
            p2 = &p[j];
            index = p1->type * n_color + p2->type;
            dx = p1->px - p2->px;
            dy = p1->py - p2->py;
            d = dx * dx + dy * dy + 1e-6f;
            r = radius[index];
            if (d < r * r)
            {
                float g = gravity[index];
                float d2 = sqrtf(d);
                p1->fx += (g / d2) * dx;
                p1->fy += (g / d2) * dy;
            }
        }

        if (p1->px < 0)
        {
            p1->fx += (0 - p1->px) * edge_strength;
        }
        else if (p1->px > width)
        {
            p1->fx += (width - p1->px) * edge_strength;
        }

        if (p1->py < 0)
        {
            p1->fy += (0 - p1->py) * edge_strength;
        }
        else if (p1->py > height)
        {
            p1->fy += (height - p1->py) * edge_strength;
        }
    }

    for (i = 0; i < n; i++)
    {
        int x, y, idx_img, idx_color;
        p1 = &p[i];
        p1->vx = p1->vx * (1 - viscosity) + time_scale * p1->fx;
        p1->vy = p1->vy * (1 - viscosity) + time_scale * p1->fy;
        p1->px += p1->vx;
        p1->py += p1->vy;
        p1->fx = p1->fy = 0;
    }
}

void particles_update_fast(Particle *p, int n, float *gravity, float *radius,
                           int n_color, int width, int height, float edge_strength, float viscosity, float time_scale,
                           int *buf_start, int *buf_end, int *buf_index, int block_size, float max_dist)
{

    int i, j;
    int w2, h2;
    int range;
    Particle *p1, *p2;
    w2 = width / block_size;
    h2 = width / block_size;

    range = (int)(max_dist / block_size) + 2;

    for (i = 0; i < w2 * h2; i++)
    {
        buf_start[i] = buf_end[i] = 0;
    }

    for (i = 0; i < n; i++)
    {
        int x, y;
        buf_index[i] = 0;
        x = (int)(p[i].px / block_size);
        y = (int)(p[i].py / block_size);
        if (x < 0)
            x = 0;
        else if (x >= w2)
            x = w2 - 1;
        if (y < 0)
            y = 0;
        else if (y >= h2)
            y = h2 - 1;
        p[i].index = y * w2 + x;
        buf_end[p[i].index]++;
    }

    for (i = 1; i < w2 * h2; i++)
    {
        buf_end[i] += buf_end[i - 1];
    }

    for (i = 1; i < w2 * h2; i++)
    {
        buf_start[i] = buf_end[i - 1];
    }

    for (i = 0; i < n; i++)
    {
        int idx;
        idx = p[i].index;
        buf_index[buf_start[idx]] = i;
        buf_start[idx]++;
    }

    buf_start[0] = 0;
    for (i = 1; i < w2 * h2; i++)
    {
        buf_start[i] = buf_end[i - 1];
    }

    for (i = 0; i < n; i++)
    {
        int xc, yc, xs, ys, xe, ye, x, y;
        p1 = &p[i];
        xc = p1->index % w2;
        yc = p1->index / w2;
        xs = xc - range;
        xe = xc + range + 1;
        ys = yc - range;
        ye = yc + range + 1;

        if (xs < 0)
            xs = 0;
        else if (xe > w2)
            xe = w2;

        if (ys < 0)
            ys = 0;
        else if (ye > h2)
            ye = h2;

        for (x = xs; x < xe; x++)
        {
            for (y = ys; y < ye; y++)
            {
                int idx = y * w2 + x;
                for (int k = buf_start[idx]; k < buf_end[idx]; k++)
                {
                    int index;
                    float dx, dy, d, r;
                    p2 = &p[buf_index[k]];
                    if (p1 == p2)
                        continue;
                    index = p1->type * n_color + p2->type;
                    dx = p1->px - p2->px;
                    dy = p1->py - p2->py;
                    d = dx * dx + dy * dy + 1e-6f;
                    r = radius[index];
                    if (d < r * r)
                    {
                        float g = gravity[index];
                        float d2 = sqrtf(d);
                        p1->fx += (g / d2) * dx;
                        p1->fy += (g / d2) * dy;
                    }
                }
            }
        }

        if (p1->px < 0)
        {
            p1->fx += (0 - p1->px) * edge_strength;
        }
        else if (p1->px > width)
        {
            p1->fx += (width - p1->px) * edge_strength;
        }

        if (p1->py < 0)
        {
            p1->fy += (0 - p1->py) * edge_strength;
        }
        else if (p1->py > height)
        {
            p1->fy += (height - p1->py) * edge_strength;
        }
    }

    for (i = 0; i < n; i++)
    {
        int x, y, idx_img, idx_color;
        p1 = &p[i];
        p1->vx = p1->vx * (1 - viscosity) + time_scale * p1->fx;
        p1->vy = p1->vy * (1 - viscosity) + time_scale * p1->fy;
        p1->px += p1->vx;
        p1->py += p1->vy;
        p1->fx = p1->fy = 0;
    }
}
