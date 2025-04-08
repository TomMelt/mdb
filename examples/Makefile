# default make will build cpu only e.g.
# $ make
# which is equivalent to
# $ make cpu
# If you want to build the gpu example, specify gpu or all e.g.,
# $ make all
# or
# $ make gpu

FC:=mpif90
CC:=mpicc
CXX:=mpic++
FLAGS=-g -O0
.PHONY: all cpu gpu

cpu: simple-mpi.exe simple-mpi-cpp.exe simple-memory.exe
gpu: saxpy-mpi.exe
all: cpu gpu

simple-mpi.exe: simple-mpi.f90
	$(FC) $(FLAGS) $^ -o $@

simple-mpi-cpp.exe: simple-mpi-cpp.cpp
	$(CXX) $(FLAGS) $^ -o $@

simple-memory.exe: simple-memory.c
	$(CC) $(FLAGS) $^ -o $@

saxpy-mpi.exe: saxpy-mpi.cu
	$(CXX) $(FLAGS) $^ -o $@

clean:
	rm -f *.exe
