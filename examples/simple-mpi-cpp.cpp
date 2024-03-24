# include <cstdlib>
# include <ctime>
# include <iostream>
# include <mpi.h>
# include <unistd.h>

using namespace std;


void leveltwo(){
  cout << "in level 2" << endl;
}

void levelone(){
  cout << "in level 1" << endl;
  MPI_Barrier(MPI_COMM_WORLD);
  leveltwo();
}

int main(void){
  int process_rank, size_of_cluster;
  float var;

  var = 0.;

  MPI_Init(NULL, NULL);
  MPI_Comm_size(MPI_COMM_WORLD, &size_of_cluster);
  MPI_Comm_rank(MPI_COMM_WORLD, &process_rank);

  var = 10.*process_rank;

  if (process_rank == 0){
    cout << "process 0 sleeping for 3s..." << endl;

    for (int i = 0; i < 3; ++i) {
      sleep(1);
      cout << i << " s..." << endl;
    }
  }

  MPI_Barrier(MPI_COMM_WORLD);
  levelone();

  cout << "internal process: " << process_rank << " of " << size_of_cluster << endl;
  cout <<  "var = " << var << endl;

  MPI_Finalize();
  return 0;
}
