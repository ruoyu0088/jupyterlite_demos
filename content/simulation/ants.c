#include <math.h>
#include <stdlib.h>

#define StatusSearch 1
#define StatusAtFood 2
#define StatusGoHome 3
#define StatusAtHome 4

typedef struct _Ant
{
    float x;
    float y;
    float x2;
    float y2;
    float angle;
    float food_chemical;
    float home_chemical;
    int clock;
    int status;
} Ant;

void diffuse(float *m1, float *m2, float k, float d, int width, int height)
{
    int i, j, di, dj;
    for (i = 0; i < height; i++)
    {
        for (j = 0; j < width; j++)
        {
            m2[i * width + j] = 0.0f;
        }
    }

    for (i = 0; i < height; i++)
    {
        for (j = 0; j < width; j++)
        {
            int idx = i * width + j;
            for (di = -1; di < 2; di++)
            {
                for (dj = -1; dj < 2; dj++)
                {
                    int i2, j2, idx2;
                    i2 = i + di;
                    j2 = j + dj;
                    idx2 = i2 * width + j2;

                    if (i2 == i && j2 == j)
                    {
                        m2[idx] += m1[idx2] * (1 - k);
                    }
                    else if (i2 >= 0 && i2 < height && j2 >= 0 && j2 < width)
                    {
                        m2[idx] += m1[idx2] * k / 8.0f;
                    }
                }
            }
        }
    }

    for (i = 0; i < height; i++)
    {
        for (j = 0; j < width; j++)
        {
            int idx = i * width + j;
            m1[idx] = m2[idx] * d;
        }
    }
}

float myrandom()
{
    return (float)(rand() % 1000) * 0.001f;
}

void set_angle(Ant *ant, float angle, float ant_length)
{
    ant->angle = angle;
    ant->x2 = ant->x + cosf(ant->angle) * ant_length;
    ant->y2 = ant->y + sinf(ant->angle) * ant_length;
}

void get_chemical_at(float x, float y, float angle, float *food_chemical, float *home_chemical, int width, int height, float ant_length, float *pf, float *ph)
{
    int k;
    float dx, dy, f, h;
    dx = cosf(angle) * ant_length;
    dy = sinf(angle) * ant_length;
    f = 0.0f;
    h = 0.0f;
    for (k = 1; k < 8; k++)
    {
        int i = (int)(x + dx * k);
        int j = (int)(y + dy * k);
        if (i >= 0 && i < width && j >= 0 && j < height)
        {
            int idx;
            idx = j * width + i;
            f += food_chemical[idx];
            h += home_chemical[idx];
        }
    }
    *pf = f;
    *ph = h;
}

void wiggle(Ant *ant, float *food_chemical, float *home_chemical, int width, int height, float ant_length)
{
    float f1, h1, f2, h2, f3, h3, dx, dy;
    float c1, c2, c3;
    float limit;
    get_chemical_at(ant->x, ant->y, ant->angle, food_chemical, home_chemical, width, height, ant_length, &f1, &h1);
    get_chemical_at(ant->x, ant->y, ant->angle + 0.25f * M_PI, food_chemical, home_chemical, width, height, ant_length, &f2, &h2);
    get_chemical_at(ant->x, ant->y, ant->angle - 0.25f * M_PI, food_chemical, home_chemical, width, height, ant_length, &f3, &h3);
    c1 = c2 = c3 = 0.0f;
    if (ant->status == StatusGoHome)
    {
        c1 = h1;
        c2 = h2;
        c3 = h3;
    }
    else if (ant->status == StatusSearch)
    {
        c1 = f1;
        c2 = f2;
        c3 = f3;
    }

    limit = 0.002f;
    if (c1 < limit && c2 < limit && c3 < limit || myrandom() < 0.2f)
    {
        set_angle(ant, ant->angle + (myrandom() - 0.5f) * (M_PI * 0.25f), ant_length);
    }
    else if (c2 > c1 && c2 > c3)
    {
        set_angle(ant, ant->angle + M_PI * 0.25f, ant_length);
    }
    else if (c3 > c1 && c3 > c2)
    {
        set_angle(ant, ant->angle - M_PI * 0.25f, ant_length);
    }

    dx = ant->x2 - ant->x;
    dy = ant->y2 - ant->y;
    ant->x += dx;
    ant->x2 += dx;
    ant->y += dy;
    ant->y2 += dy;
    if (ant->x <= 0 || ant->y <= 0)
    {
        set_angle(ant, ant->angle + M_PI, ant_length);
    }
    else if (ant->x > width - 1 || ant->y > height - 1)
    {
        set_angle(ant, ant->angle - M_PI, ant_length);
    }
}

void move_ant(Ant *ant, float *food_chemical, float *home_chemical, int *home, float *food, int width, int height, float ant_length)
{
    int x, y, idx;
    wiggle(ant, food_chemical, home_chemical, width, height, ant_length);
    x = (int)ant->x;
    y = (int)ant->y;
    if (x < 0 || x >= width || y < 0 || y >= height)
    {
        return;
    }
    idx = y * width + x;
    home_chemical[idx] += ant->home_chemical;
    food_chemical[idx] += ant->food_chemical;
    switch (ant->status)
    {
    case StatusGoHome:
        ant->food_chemical *= 0.98f;
        if (home[idx] == 1)
        {
            ant->status = StatusAtHome;
            ant->food_chemical = 0;
            ant->clock = 40;
            ant->home_chemical = 1;
        }
        break;

    case StatusAtHome:
        ant->clock -= 1;
        if (ant->clock == 0)
            ant->status = StatusSearch;
        break;

    case StatusSearch:
        ant->home_chemical *= 0.98f;
        if (food[idx] > 0.0f)
        {
            ant->status = StatusAtFood;
            ant->home_chemical = 0.0f;
            ant->clock = 30;
        }
        break;

    case StatusAtFood:
        if (food[idx] > 0)
        {
            ant->food_chemical += 0.1f;
            food[idx] -= 0.1f;
        }
        ant->clock -= 1;
        if (ant->clock == 0)
        {
            ant->status = StatusGoHome;
        }
        break;
    }
}

void ants_update(Ant *ants, int n, float *food_chemical, float *food_chemical2, float *home_chemical, float *home_chemical2, int *home, float *food, int width, int height, float ant_length)
{
    for (int i = 0; i < n; i++)
    {
        move_ant(&ants[i], food_chemical, home_chemical, home, food, width, height, ant_length);
    }
    diffuse(food_chemical, food_chemical2, 0.5f, 0.99f, width, height);
    diffuse(home_chemical, home_chemical2, 0.5f, 0.995f, width, height);
}