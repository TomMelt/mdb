#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <hip/hip_runtime.h>
#include <mpi.h>

#define HIP_CHECK(call)                                                       \
    do {                                                                      \
        hipError_t err = call;                                                \
        if (err != hipSuccess) {                                              \
            fprintf(stderr, "HIP error at %s:%d: %s\n", __FILE__, __LINE__,  \
                    hipGetErrorString(err));                                   \
            MPI_Abort(MPI_COMM_WORLD, 1);                                     \
        }                                                                     \
    } while (0)

__global__ void saxpy_kernel(int n, float a, const float* x, float* y) {
    int i = blockDim.x * blockIdx.x + threadIdx.x;
    if (i < n)
        y[i] = a * (x[i] + y[i]);
}

int main(int argc, char* argv[]) {
    MPI_Init(&argc, &argv);

    int rank, nprocs;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &nprocs);

    const long long total_n = (argc > 1) ? atoll(argv[1]) : (1LL << 20);
    const float a = 2.0f;

    if (total_n % nprocs != 0) {
        if (rank == 0)
            fprintf(stderr, "Error: array length %lld not divisible by %d ranks\n",
                    total_n, nprocs);
        MPI_Finalize();
        return 1;
    }

    const long long local_n = total_n / nprocs;

    int num_devices;
    HIP_CHECK(hipGetDeviceCount(&num_devices));
    HIP_CHECK(hipSetDevice(rank % num_devices));

    if (rank == 0)
        printf("Running SAXPY: total_n=%lld, nprocs=%d, local_n=%lld, GPUs per node=%d\n",
               total_n, nprocs, local_n, num_devices);

    float* h_x = (float*)malloc(local_n * sizeof(float));
    float* h_y = (float*)malloc(local_n * sizeof(float));

    if (rank == 0){
        for (long long i = 0; i < local_n; i++) {
            h_x[i] = std::pow(std::sin(1.0f * i/6.),2.0);
            h_y[i] = std::pow(std::cos(1.0f * i/6.),2.0);
        }
    }
    if (rank == 1){
        for (long long i = 0; i < local_n; i++) {
            h_x[i] = std::pow(std::cos(1.0f * i/6.),2.0);
            h_y[i] = std::pow(std::sin(1.0f * i/6.),2.0);
        }
    }

    float *d_x, *d_y;
    HIP_CHECK(hipMalloc(&d_x, local_n * sizeof(float)));
    HIP_CHECK(hipMalloc(&d_y, local_n * sizeof(float)));

    HIP_CHECK(hipMemcpy(d_x, h_x, local_n * sizeof(float), hipMemcpyHostToDevice));
    HIP_CHECK(hipMemcpy(d_y, h_y, local_n * sizeof(float), hipMemcpyHostToDevice));

    int threads = 256;
    int blocks = (local_n + threads - 1) / threads;

    MPI_Barrier(MPI_COMM_WORLD);
    double t0 = MPI_Wtime();

    hipLaunchKernelGGL(saxpy_kernel, dim3(blocks), dim3(threads), 0, 0, local_n, a, d_x, d_y);
    HIP_CHECK(hipGetLastError());
    HIP_CHECK(hipDeviceSynchronize());

    MPI_Barrier(MPI_COMM_WORLD);
    double t1 = MPI_Wtime();

    HIP_CHECK(hipMemcpy(h_y, d_y, local_n * sizeof(float), hipMemcpyDeviceToHost));

    // expected: y = a*x + y_orig = 2*1 + 2 = 4
    const float expected = 1.0f * a;
    double local_diff_sum = 0.0;
    for (long long i = 0; i < local_n; i++)
        local_diff_sum += fabs((double)h_y[i] - (double)expected);

    double global_diff_sum = 0.0;
    MPI_Reduce(&local_diff_sum, &global_diff_sum, 1, MPI_DOUBLE, MPI_SUM,
               0, MPI_COMM_WORLD);

    if (rank == 0) {
        printf("Kernel time: %.6f s\n", t1 - t0);
        if (global_diff_sum < 1e-6)
            printf("PASSED: global difference sum = %e\n", global_diff_sum);
        else
            printf("FAILED: global difference sum :( = %e\n", global_diff_sum);
    }

    HIP_CHECK(hipFree(d_x));
    HIP_CHECK(hipFree(d_y));
    free(h_x);
    free(h_y);

    MPI_Finalize();
    return 0;
}
