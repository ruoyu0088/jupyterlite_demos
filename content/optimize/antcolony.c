#include <stdlib.h>
#include <math.h>

void del_val(int *x, int n, int v)
{
    for (int i = 0; i < n; i++)
    {
        if (x[i] == v)
        {
            for (int j = i; j < n - 1; j++)
            {
                x[j] = x[j + 1];
            }
        }
    }
}

double frandom()
{
    return (double)rand() / RAND_MAX;
}

int choice(int *x, double *w, int n)
{
    double sum_w = 0;
    double sum_p;
    double toss;
    int i;
    for (i = 0; i < n; i++)
    {
        sum_w += w[i];
    }
    if (sum_w == 0)
    {
        return x[rand() % n];
    }

    toss = frandom();
    sum_p = 0;
    for (i = 0; i < n; i++)
    {
        double p = w[i] / sum_w;
        if (toss <= sum_p + p)
        {
            return x[i];
        }
        else
        {
            sum_p += p;
        }
    }
    return x[n - 1];
}

double ant_travel(double *dist_matrix, double *pheromone_matrix, double alpha, double beta, int n,
                  int *to_travel, int *path, double *weights)
{
    int i, j;
    int location;
    double dist;
    location = rand() % n;
    for (i = 0; i < n; i++)
    {
        to_travel[i] = i;
    }
    del_val(to_travel, n, location);

    for (i = 0; i < n; i++)
    {
        path[i] = 0;
        weights[i] = 0.0;
    }

    path[0] = location;
    dist = 0.0;

    for (i = 1; i < n; i++)
    {
        int next_location;
        double sum_weight = 0.0;
        for (j = 0; j < n - i; j++)
        {
            double a, d, p;
            next_location = to_travel[j];
            d = dist_matrix[location * n + next_location];
            p = pheromone_matrix[location * n + next_location];
            a = pow(p, alpha) / pow(d, beta);
            weights[j] = a;
            sum_weight += a;
        }
        next_location = choice(to_travel, weights, n - i);
        dist += dist_matrix[location * n + next_location];
        path[i] = next_location;
        del_val(to_travel, n, next_location);
        location = next_location;
    }
    return dist;
}

double ant_colony_optimize(double *dist_matrix, int iter_count, double Q, double alpha, double beta, double rho, int closed,
                           double *pheromone_matrix, int *to_travel, int *path, int *best_path, double *weights, double min_dist, int n)
{
    int i, j;
    double dist;

    for (i = 0; i < iter_count; i++)
    {
        dist = ant_travel(dist_matrix, pheromone_matrix, alpha, beta, n, to_travel, path, weights);
        if (closed)
        {
            dist += dist_matrix[path[n - 1] * n + path[0]];
        }

        if (dist < min_dist)
        {
            min_dist = dist;
            for (j = 0; j < n; j++)
            {
                best_path[j] = path[j];
            }
        }

        for (j = 0; j < n * n; j++)
        {
            pheromone_matrix[j] *= rho;
        }

        for (j = 0; j < n - 1; j++)
        {
            int s, e;
            s = path[j];
            e = path[j + 1];
            pheromone_matrix[s * n + e] += Q / dist;
            pheromone_matrix[e * n + s] += Q / dist;
        }

        if (closed)
        {
            int s, e;
            s = path[n - 1];
            e = path[0];
            pheromone_matrix[s * n + e] += Q / dist;
            pheromone_matrix[e * n + s] += Q / dist;
        }
    }

    return min_dist;
}