#include <complex.h>

void julia_miim(double cr, double ci, double zr, double zi, double * p_, int n, unsigned char * grid, int resolution, int max_count){
    double _Complex * p;
    double _Complex z;
    double _Complex c;
    int j = 1;
    int i = 0;
    int k = 0;
    z = zr + I * zi;
    c = cr + I * ci;
    p = (double _Complex *) p_;
    p[0] = z;
    while(1){
        if(i >= j) break;
        z = p[i];
        i ++;
        z = csqrt(z - c);
        zr = creal(z);
        zi = cimag(z);
        if(zr <= -2 || zr >= 2 || zi <= -2 || zi >= 2) break;
        for(k=0;k<2;k++){
            int col = (int)((resolution * (zr + 2.0) / 4.0));
            int row = (int)((resolution * (-zi + 2.0) / 4.0));
            int index = row * resolution + col;
            if(grid[index] < max_count){
                grid[index] ++;
                p[j] = z;
                j ++;
                if(j == n){
                    return;
                }
            }
            z = -1 * z;
            zr = creal(z);
            zi = cimag(z);
        }
    }
}
