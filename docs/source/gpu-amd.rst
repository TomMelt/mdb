.. Copyright 2023-2026 Tom Meltzer. See the top-level COPYRIGHT file for
   details.

.. _gpu_amd:

Debugging AMD GPU Kernels
=========================

In this tutorial we will explore how to debug GPU kernels on AMD hardware, for MPI applications.

.. note::

   If your GPU code does not use MPI, or it can be run serially, you may find it easier to use a
   serial debugger e.g., ``rocgdb``.

If this is your first time debugging MPI code please see the :quickstart guide:`_quick_start`. This
runs through a CPU-only MPI code running on 8 processes.

Compile with Debug Symbols
==========================

Before we can debug with ``mdb`` we first need to compile our code with debug symbols. There is an
example HIP MPI code included in the examples directory called ``saxpy-hip-mpi.cpp``. To build it we
can run ``make hip`` from inside the examples directory

.. code-block:: console

   $ cd examples
   $ make hip

You should output like this

.. code-block:: console

   OMPI_CXX=hipcc mpic++ -ggdb -O0 saxpy-hip-mpi.cpp -o saxpy-hip-mpi.exe

And you should now have a binary called ``saxpy-hip-mpi.exe``. The example Makefile includes the
flags ``-ggdb`` and ``-O0`` which tells the compiler to enable debugging information for use by GDB
and disable code optimizations, respectively.

.. note::

   Please make sure you have loaded appropriate modules, if you are on a HPC system. E.g., ``module
   load rocm openmpi``

Launch the Debugger
===================

Now that we have our binary with debug symbols, we will launch the debug session.

.. code-block:: console

   $ mdb launch -n 2 -t ./saxpy-hip-mpi.exe -b rocgdb

``mdb`` comes with many backends, in our case we want to use the ``rocgdb`` debugger as this will
allow us to stop inside HIP GPU kernels. For this example code we will run with 2 processes. It
should look like the following:

.. code-block:: console

   $ mdb launch -n 2 -t ./saxpy-hip-mpi.exe -b rocgdb
   running on host: 127.0.1.1
   to connect to the debugger run:
   mdb attach -h 127.0.1.1 -p 2000

   connecting to debuggers ... (2/2)
   all debug clients connected

Attach the Debugger
===================

Now, we will attach to the debugger from a different terminal. Run the following command, from the
same directory that you have launched the debugger (this will be important later on in the
tutorial, when we try to plot the data, but isn't normally required).

.. code-block:: console

   $ mdb attach

.. note::

   You can use ``mdb attach -h 127.0.1.1 -p 2000`` as suggested in the output of ``mdb launch`` but
   if you are attaching on the same node as you run the launcher, it will default the other options.

Inspecting Memory
=================

Now we are in the debugger, let's set a breakpoint in our kernel and see if we can inspect the GPU
memory directly.

.. code-block:: console

   mdb - mpi debugger - built on various backends. Type ? for more info. To exit interactive mode
   type "q", "quit", "Ctrl+D" or "Ctrl+]".
   (mdb 0-1) command b 19
   0:      No compiled code for line 19 in the current file.
   0:      Breakpoint 2 (19) pending.
   ************************************************************************
   1:      No compiled code for line 19 in the current file.
   1:      Breakpoint 2 (19) pending.

We set a breakpoint with command ``command b 19``. This will set the breakpoint on both processes (0
and 1). Note in the output we see ``No compiled code for line 19 in the current file. Breakpoint 2
(19) pending.``. This is telling us that the debug symbols are not currently loaded, but when we
(and if) we get there, they will be loaded by ``rocgdb``. Let's continue code execution to reach the
breakpoint.

.. code-block:: console

   (mdb 0-1) command c
   0:      Continuing.
   0:      [New Thread 0x7fffeffff640 (LWP 2180043)]
   0:      [New Thread 0x7fffef7fe640 (LWP 2180045)]
   0:      [New Thread 0x7ffdeebff640 (LWP 2180046)]
   0:      [Thread 0x7ffdeebff640 (LWP 2180046) exited]
   0:      [New Thread 0x7ffdee3fe640 (LWP 2180048)]
   0:      [New Thread 0x7ffded885640 (LWP 2180052)]
   0:      [Thread 0x7ffded885640 (LWP 2180052) exited]
   0:      Running SAXPY: total_n=1048576, nprocs=2, local_n=524288, GPUs per node=2
   0:      [New Thread 0x7ffded885640 (LWP 2180063)]
   0:      [Thread 0x7ffded885640 (LWP 2180063) exited]
   0:      [New Thread 0x7ffdecaff640 (LWP 2180065)]
   0:      [Switching to thread 10, lane 0 (AMDGPU Lane 1:4:1:1/0 (0,0,0)[0,0,0])]
   0:
   0:      Thread 10 "saxpy_kernel" hit Breakpoint 2, with lanes [0-63], saxpy_kernel (
   0:          n=524288, a=2, x=0x7ffdcb000000, y=0x7ffdcac00000) at saxpy-hip-mpi.cpp:19
   0:      19          if (i < n)
   ************************************************************************
   1:      Continuing.
   1:      [New Thread 0x7fffeffff640 (LWP 2180041)]
   1:      [New Thread 0x7fffef7fe640 (LWP 2180042)]
   1:      [New Thread 0x7fffeeffd640 (LWP 2180044)]
   1:      [Thread 0x7fffeeffd640 (LWP 2180044) exited]
   1:      [New Thread 0x7fffee7fc640 (LWP 2180047)]
   1:      [New Thread 0x7fffed89c640 (LWP 2180051)]
   1:      [Thread 0x7fffed89c640 (LWP 2180051) exited]
   1:      [New Thread 0x7fffed89c640 (LWP 2180064)]
   1:      [Thread 0x7fffed89c640 (LWP 2180064) exited]
   1:      [New Thread 0x7fffecaef640 (LWP 2180066)]
   1:      [Switching to thread 10, lane 0 (AMDGPU Lane 2:3:1:1/0 (0,0,0)[0,0,0])]
   1:
   1:      Thread 10 "saxpy_kernel" hit Breakpoint 2, with lanes [0-63], saxpy_kernel (
   1:          n=524288, a=2, x=0x7ffde4200000, y=0x7ffdd4a00000) at saxpy-hip-mpi.cpp:19
   1:      19          if (i < n)

   (mdb 0-1) command 0 list
   0:      14              }                                                                     \
   0:      15          } while (0)
   0:      16
   0:      17      __global__ void saxpy_kernel(int n, float a, const float* x, float* y) {
   0:      18          int i = blockDim.x * blockIdx.x + threadIdx.x;
   0:      19          if (i < n)
   0:      20              y[i] = a * (x[i] + y[i]);
   0:      21      }
   0:      22
   0:      23      int main(int argc, char* argv[]) {



We are now at line 19, and I have run the ``list`` command to view the source. We can see that we
are correctly inside of the ``saxpy_kernel`` kernel. Let's try inspecting some memory. This memory
is on the AMD GPU but we can access it via ``rocgdb``.

.. code-block:: console

   (mdb 0-1) command thread
   0:      [Current thread is 10, lane 0 (AMDGPU Lane 1:4:1:1/0 (0,0,0)[0,0,0])]
   ************************************************************************
   1:      [Current thread is 10, lane 0 (AMDGPU Lane 2:3:1:1/0 (0,0,0)[0,0,0])]

   (mdb 0-1) command print i
   0:      $4 = 0
   ************************************************************************
   1:      $4 = 0

First we can inspect our current thread. Both processes are on the first thread of each GPU.
Therefore, they both have index ``i=0``. But we can switch process 0 to thread 128 for example.

.. code-block:: console

   (mdb 0-1) command 0 thread 128
   0:      [Switching to thread 128, lane 0 (AMDGPU Lane 1:4:1:119/0 (29,0,0)[128,0,0])]
   0:      #0  saxpy_kernel (n=524288, a=2, x=0x7ffdcb000000, y=0x7ffdcac00000)
   0:          at saxpy-hip-mpi.cpp:19
   0:      19          if (i < n)

   (mdb 0-1) command thread
   0:      [Current thread is 128, lane 0 (AMDGPU Lane 1:4:1:119/0 (29,0,0)[128,0,0])]
   ************************************************************************
   1:      [Current thread is 10, lane 0 (AMDGPU Lane 2:3:1:1/0 (0,0,0)[0,0,0])]

   (mdb 0-1) command print i
   0:      $5 = 7552
   ************************************************************************
   1:      $5 = 0

Now we can see that ``i=7552`` on process 0 as we are on a different thread. ``i`` is set in the
line above ``int i = blockDim.x * blockIdx.x + threadIdx.x;``. From the ``thread`` command on
process 0 we have ``Current thread is 128, lane 0 (AMDGPU Lane 1:4:1:119/0 (29,0,0)[128,0,0])``. The
important part here is ``(29,0,0)[128,0,0]`` which tells us that we are in block 29 and the 128th
thread e.g., ``256 * 29 + 128 = 7552``.

Although we can jump threads, we can also inspect memory that is available to all threads without
changing to each thread individually. The array ``x`` is in global memory, and therefore we can see
it from any of the threads. Let's inspect the first 100 values of ``x`` on each process (and hence
each GPU).

.. code-block:: console

   (mdb 0-1) command print x[0]@100
   0:      $1 = {0, 0.0275215264, 0.107056372, 0.229848847, 0.382381201, 0.547861755,
   0:        0.708073437, 0.845379055, 0.944663286, 0.99499625, 0.990836978, 0.932643414,
   0:        0.826821804, 0.685021639, 0.522853196, 0.3581689, 0.20909825, 0.0920518413,
   0:        0.0199148562, 0.000628574402, 0.0363161489, 0.123048872, 0.251278669,
   0:        0.40688926, 0.572750032, 0.730602026, 0.863067925, 0.955565155, 0.997910917,
   0:        0.985443652, 0.919535756, 0.807442844, 0.661504686, 0.497787148,
   0:        0.334313214, 0.189079076, 0.0780730173, 0.0135152638, 0.00251271715,
   0:        0.0462766103, 0.139989138, 0.273333877, 0.431631386, 0.597455323,
   0:        0.75255084, 0.87984395, 0.965321541, 0.999573708, 0.978829741, 0.905373275,
   0:        0.787290812, 0.637581646, 0.472726673, 0.310874104, 0.169841647,
   0:        0.0651550442, 0.00833883788, 0.00564769097, 0.0573778674, 0.157834589,
   0:        0.295958966, 0.456545442, 0.621915638, 0.773864627, 0.89566493, 0.973908007,
   0:        0.99998039, 0.971011937, 0.890191555, 0.76641649, 0.613312721, 0.447734773,
   0:        0.287910491, 0.151434332, 0.0533304028, 0.00439859414, 0.0100256139,
   0:        0.0695920065, 0.176540345, 0.319097102, 0.481568724, 0.646069407,
   0:        0.794489861, 0.910491109, 0.981302917, 0.999130011, 0.962009847,
   0:        0.874028742, 0.744872332, 0.588758886, 0.422874272, 0.265480161,
   0:        0.133903414, 0.042628821, 0.00170443999, 0.0156354774, 0.0828883201,
   0:        0.196059361, 0.342690051, 0.506638348}
   ************************************************************************
   1:      $1 = {1, 0.972478449, 0.892943621, 0.770151138, 0.617618799, 0.452138215,
   1:        0.291926593, 0.154620931, 0.0553367175, 0.00500375172, 0.00916299783,
   1:        0.067356579, 0.173178196, 0.314978331, 0.477146804, 0.6418311, 0.790901721,
   1:        0.907948136, 0.980085135, 0.999371409, 0.963683844, 0.876951098,
   1:        0.748721302, 0.59311074, 0.427249998, 0.269397974, 0.13693206, 0.0444348678,
   1:        0.00208907365, 0.0145563539, 0.0804642364, 0.192557171, 0.338495314,
   1:        0.502212822, 0.665686786, 0.810920894, 0.921926975, 0.986484766,
   1:        0.997487307, 0.953723371, 0.860010862, 0.726666152, 0.568368614,
   1:        0.402544647, 0.247449175, 0.120156042, 0.034678448, 0.000426291721,
   1:        0.0211702604, 0.0946267322, 0.212709159, 0.362418324, 0.527273297,
   1:        0.689125896, 0.830158353, 0.934844971, 0.991661191, 0.994352281,
   1:        0.942622125, 0.842165411, 0.704041004, 0.543454587, 0.378084362,
   1:        0.226135373, 0.10433507, 0.0260919854, 1.95868033e-05, 0.0289880857,
   1:        0.109808452, 0.233583495, 0.386687279, 0.552265227, 0.712089479,
   1:        0.848565698, 0.946669579, 0.995601416, 0.98997438, 0.930408001, 0.823459685,
   1:        0.680902898, 0.518431246, 0.353930593, 0.205510139, 0.0895089209,
   1:        0.0186970662, 0.000869981421, 0.0379901752, 0.125971228, 0.255127668,
   1:        0.411241144, 0.577125728, 0.734519839, 0.866096556, 0.957371175,
   1:        0.998295546, 0.98436451, 0.917111695, 0.803940654, 0.657309949, 0.493361622}

This is OK, but it's not very easy to see if these values are correct. So let's dump them to disk so
that we can plot them manually. We can use the ``mdb dump`` command.

.. code-block:: console

   (mdb 0-1) dump x[0]@1000
   written data to disk

Here we will dump the first 1000 elements to disk. Then we will use `bplot
<https://github.com/TomMelt/bplot>`_, a small command line plotter that I made for simple ASCII
plots of 1D data.

.. note::

   Installation of ``bplot`` is outside the scope of this tutorial. You could in principal use
   ``matplotlib`` or any other plotting tool you prefer. First you would need to read the binary
   data and convert it to the relevant data type.

First, we will check that our binary files have been written to disk using the ``ls`` command from
inside ``mdb``.

.. code-block:: console

   (mdb 0-1) !ls
    Makefile    mdb-attach.log   rank.1.log          saxpy-hip-mpi.exe   simple-memory.c      simple-mpi-cuda.mdb     simple-mpi.f90    'x[0]@1000.dmp.1'
    README.md   rank.0.log       saxpy-hip-mpi.cpp   saxpy-mpi.cu        simple-mpi-cpp.cpp   simple-mpi-script.mdb  'x[0]@1000.dmp.0'
   (mdb 0-1) !
    Makefile    mdb-attach.log   rank.1.log          saxpy-hip-mpi.exe   simple-memory.c      simple-mpi-cuda.mdb     simple-mpi.f90    'x[0]@1000.dmp.1'
    README.md   rank.0.log       saxpy-hip-mpi.cpp   saxpy-mpi.cu        simple-mpi-cpp.cpp   simple-mpi-script.mdb  'x[0]@1000.dmp.0'
   (mdb 0-1) !bplot -f 'x[0]@1000.dmp.0' -s 1,1000 -l c --plot-range=0,:200 -d f --plot-height 14
            bplot -f x[0]@1000.dmp.0 -s 1,1000 -l c --plot-range=0,:200 -d f --plot-height 14
       ┌─────────────────────────────────────────────────────────────────────────────────────────┐
   1.00┤   ▗▀▖      ▞▘      ▗▀       ▀▖      ▝▌      ▗▜       ▞▖      ▐▚      ▗▀       ▞▘      ▝▚│
   0.83┤   ▖ ▗     ▗ ▝      ▘ ▘     ▝ ▘      ▘▝        ▖     ▗ ▗      ▖ ▖     ▝ ▘     ▝ ▝      ▘ │
       │           ▖  ▘    ▗  ▘     ▘ ▝     ▝  ▖     ▘ ▗             ▗        ▖ ▝     ▗  ▘    ▝  │
   0.67┤  ▝   ▘       ▘       ▗    ▗   ▖    ▖       ▝        ▘  ▘       ▝        ▖    ▖  ▗    ▗  │
   0.50┤  ▖   ▖   ▝        ▘                   ▝    ▖   ▘   ▗   ▗    ▘   ▖   ▝                   │
       │          ▖   ▝   ▗    ▘   ▘   ▝   ▝    ▖       ▗                    ▖   ▝   ▗    ▘   ▘  │
   0.33┤  ▘   ▝        ▖       ▗  ▗        ▖       ▝        ▘    ▘  ▝    ▝        ▖       ▗  ▗   │
   0.17┤ ▗     ▖  ▘    ▗  ▘             ▘       ▝  ▖     ▘ ▗     ▗  ▘     ▖ ▝        ▘           │
       │ ▖     ▗ ▗        ▘     ▘ ▘     ▝ ▝      ▘▗      ▗ ▖      ▖▗      ▗ ▖     ▝ ▝     ▝  ▘   │
   0.00┤▞       ▄▘      ▚▞      ▝▄▘      ▚▌      ▝▖       ▚       ▗▘      ▗▞      ▝▄▘      ▚▞    │
       └┬─────────────────────┬─────────────────────┬─────────────────────┬─────────────────────┬┘
       1.0                  50.8                  100.5                 150.2               200.0
   (mdb 0-1) !bplot -f 'x[0]@1000.dmp.1' -s 1,1000 -l c --plot-range=0,:200 -d f --plot-height 14
            bplot -f x[0]@1000.dmp.1 -s 1,1000 -l c --plot-range=0,:200 -d f --plot-height 14
       ┌─────────────────────────────────────────────────────────────────────────────────────────┐
   1.00┤▚       ▀▖      ▞▚      ▗▀▖      ▞▌      ▗▘       ▞       ▝▖      ▝▚      ▗▀▖      ▞▚    │
   0.83┤ ▘     ▝ ▝        ▖     ▖ ▖     ▗ ▗      ▖▝      ▝ ▘      ▘▝      ▝ ▘     ▗ ▗     ▗  ▖   │
       │ ▝     ▘  ▖    ▝  ▖             ▖       ▗  ▘     ▖ ▝     ▝  ▖     ▘ ▗        ▖           │
   0.67┤  ▖   ▗        ▘       ▝  ▝        ▘       ▗        ▖    ▖  ▗    ▗        ▘       ▝  ▝   │
   0.50┤          ▘   ▗   ▝    ▖   ▖   ▗   ▗    ▘       ▝                    ▘   ▗   ▝    ▖   ▖  │
       │  ▘   ▘   ▗        ▖                   ▗    ▘   ▖   ▝   ▝    ▖   ▘   ▗                   │
   0.33┤  ▗   ▖       ▖       ▝    ▝   ▘    ▘       ▗        ▖  ▖       ▗        ▘    ▘  ▝    ▝  │
   0.17┤           ▘  ▖    ▝  ▖     ▖ ▗     ▗  ▘     ▖ ▝             ▝        ▘ ▗     ▝  ▖    ▗  │
       │   ▘ ▝     ▝ ▗      ▖ ▖     ▗ ▖      ▖▗        ▘     ▝ ▝      ▘ ▘     ▗ ▖     ▗ ▗      ▖ │
   0.00┤   ▝▄▘      ▚▖      ▝▄       ▄▘      ▗▌      ▝▟       ▚▘      ▐▞      ▝▄       ▚▖      ▗▞│
       └┬─────────────────────┬─────────────────────┬─────────────────────┬─────────────────────┬┘
       1.0                  50.8                  100.5                 150.2               200.0

As expected, each GPU (each process) has it's own ``x`` array. GPU 0 (process 0) was initialized
with ``sin^2(i/6)`` and GPU 1 (process 1) is initialized with ``cos^2(i/6)``, as indicated in the
source code ``saxpy-hip-mpi.cpp:54-65``.

.. code-block:: cpp

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

There is plenty more you can do with the ``rocgdb`` debugger. I hope this tutorial provides some of the basics. Happy bug-hunting :)
