#include <stdio.h>
#include <mpi.h>

__global__
void saxpy(int n, float a, float *x, float *y)
{
  int i = blockIdx.x*blockDim.x + threadIdx.x;
  if (i < n) y[i] = a*x[i] - y[i];
}

int main(void)
{
  int N = 1<<10;
  float *x, *y, *d_x, *d_y;
  x = (float*)malloc(N*sizeof(float));
  y = (float*)malloc(N*sizeof(float));

  int process_rank, size_of_cluster;

  MPI_Init(NULL, NULL);
  MPI_Comm_size(MPI_COMM_WORLD, &size_of_cluster);
  MPI_Comm_rank(MPI_COMM_WORLD, &process_rank);

  printf("process rank = %d\n", process_rank);

  if (process_rank >= 0){
    cudaMalloc(&d_x, N*sizeof(float)); 
    cudaMalloc(&d_y, N*sizeof(float));

    for (int j = 0; j < 2000; ++j) {
      for (int i = 0; i < N; i++) {
        x[i] = 1.0f * i * (process_rank + 1);
        y[i] = 2.0f * i * (process_rank + 1);
      }
      cudaMemcpy(d_x, x, N*sizeof(float), cudaMemcpyHostToDevice);
      cudaMemcpy(d_y, y, N*sizeof(float), cudaMemcpyHostToDevice);

      // Perform SAXPY on 1M elements
      saxpy<<<(N+255)/256, 256>>>(N, 2.0f, d_x, d_y);

      cudaMemcpy(y, d_y, N*sizeof(float), cudaMemcpyDeviceToHost);
    }

    float maxError = 0.0f;
    for (int i = 0; i < N; i++)
      maxError = max(maxError, abs(y[i]));
    printf("Max error: %f\n", maxError);

    cudaFree(d_x);
    cudaFree(d_y);
  }
  free(x);
  free(y);
  MPI_Finalize();
}
