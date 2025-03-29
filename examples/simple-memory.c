#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>


void f(void)
{
  float y = 0;
  
  int* x = malloc(10 * sizeof(int));
  x[10] = 0;        // problem 1: heap block overrun (Invalid write)
  int j = 0;
  int sum;
  if (sum>0){
    j = 10;
  }
  for (j = 0; j < 10; ++j) {
    sum = sum + j;
  }
  x[10] = 0;        // problem 1: heap block overrun (Invalid write)
                    // x[9] = 0;      // solution 1: set 10th element instead of 11th
                    // free(x);       // solution 2: free x before end of scope
}                    // problem 2: memory leak -- x not freed

int main(int argc, char** argv)
{
  int process_Rank, size_Of_Cluster;
  MPI_Init(&argc, &argv);
  MPI_Comm_size(MPI_COMM_WORLD, &size_Of_Cluster);
  MPI_Comm_rank(MPI_COMM_WORLD, &process_Rank);

  printf("Hello World from process %d of %d\n", process_Rank, size_Of_Cluster);
  f();
  return 0;
}
